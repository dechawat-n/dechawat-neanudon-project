# Import necessary modules and functions
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from ..models import *
from booking.models import *
from typing import Optional
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden, HttpResponseRedirect
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_http_methods(["POST"])
def update_user_profile(request):
    try:
        user = request.user
        
        # รับข้อมูลจาก request
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        
        # ตรวจสอบความถูกต้องของข้อมูล
        if username:
            # ตรวจสอบว่า username ซ้ำหรือไม่
            if CustomerUsers.objects.exclude(pk=user.pk).filter(username=username).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'ชื่อผู้ใช้นี้มีอยู่แล้ว'
                }, status=400)
            user.username = username
        
        if email:
            # ตรวจสอบว่า email ซ้ำหรือไม่
            if CustomerUsers.objects.exclude(pk=user.pk).filter(email=email).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'อีเมลนี้มีอยู่แล้ว'
                }, status=400)
            user.email = email
        
        if phone_number:
            # ตรวจสอบความยาวเบอร์โทรศัพท์
            if len(phone_number) != 10:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'หมายเลขโทรศัพท์ต้องมี 10 หลัก'
                }, status=400)
            user.phone_number = phone_number
        
        user.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'อัปเดตข้อมูลสำเร็จ'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)
    
@login_required
@require_http_methods(["PATCH"])
def update_user(request, user_id):
    try:
        # ตรวจสอบว่าเป็น admin หรือผู้ใช้แก้ไขข้อมูลตัวเอง
        if not request.user.is_superuser and request.user.id != user_id:
            return JsonResponse({
                'status': 'error', 
                'message': 'คุณไม่มีสิทธิ์แก้ไขข้อมูลผู้ใช้นี้'
            }, status=403)

        # แปลงข้อมูล JSON
        data = json.loads(request.body)
        
        # ดึงข้อมูลผู้ใช้
        user = CustomerUsers.objects.get(id=user_id)
        
        # อัปเดตข้อมูล
        if 'username' in data:
            # ตรวจสอบ username ซ้ำ
            if CustomerUsers.objects.exclude(pk=user.pk).filter(username=data['username']).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'ชื่อผู้ใช้นี้มีอยู่แล้ว'
                }, status=400)
            user.username = data['username']
        
        if 'email' in data:
            # ตรวจสอบ email ซ้ำ
            if CustomerUsers.objects.exclude(pk=user.pk).filter(email=data['email']).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'อีเมลนี้มีอยู่แล้ว'
                }, status=400)
            user.email = data['email']
        
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        
        if 'is_superuser' in data and request.user.is_superuser:
            user.is_superuser = data['is_superuser']
        
        user.save()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'อัปเดตข้อมูลสำเร็จ'
        })
    
    except CustomerUsers.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'ไม่พบผู้ใช้'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'ข้อมูล JSON ไม่ถูกต้อง'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def change_password(request):
    try:
        user = request.user
        
        # รับข้อมูลจาก request
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # ตรวจสอบรหัสผ่านปัจจุบัน
        if not user.check_password(current_password):
            return JsonResponse({
                'status': 'error', 
                'message': 'รหัสผ่านปัจจุบันไม่ถูกต้อง'
            }, status=400)
        
        # ตรวจสอบการยืนยันรหัสผ่าน
        if new_password != confirm_password:
            return JsonResponse({
                'status': 'error', 
                'message': 'รหัสผ่านใหม่ไม่ตรงกัน'
            }, status=400)
        
        # ตรวจสอบความยาวรหัสผ่าน
        if len(new_password) < 5:
            return JsonResponse({
                'status': 'error', 
                'message': 'รหัสผ่านต้องมีอย่างน้อย 5 ตัวอักษร'
            }, status=400)
        
        # เปลี่ยนรหัสผ่าน
        user.set_password(new_password)
        user.save()
        
        # ลงชื่อออกและเข้าสู่ระบบใหม่เพื่อรีเซ็ต session
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        return JsonResponse({
            'status': 'success', 
            'message': 'เปลี่ยนรหัสผ่านสำเร็จ'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)
# Create a logger instance
logger = logging.getLogger(__name__)
CustomerUsers = get_user_model()
def check_login(request):
    return {
        'loggedin': request.user.is_authenticated,
        'user': request.user
    }

# Home view for Thai language
def Home_th(request):
    # Render logged in home
    logged_in = check_login(request)
    return render(request, 'public/home-th.html', logged_in)

# Home view for English language
def Home_en(request):
    logged_in = check_login(request)
    return render(request, 'home-en.html', logged_in)

# Login view with CSRF protection
@csrf_protect
def LoginView(request):
    if request.method == "POST":
        # Get username, password, and remember me Checkbox from POST request
        username: str = request.POST.get("username", "")
        password: str = request.POST.get("password", "")
        remember: Optional[str] = request.POST.get("remember")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Remember me checkbox logic
            if remember:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Browser close
                
            request.session['last_login'] = timezone.now().isoformat()
            request.session['ip'] = request.META.get('REMOTE_ADDR')
            return redirect('/')
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return redirect('login-th')

    return render(request, 'public/login-th.html')

#เพิ่มมา
@login_required
def my_reservations(request):
    logged_in = check_login(request)
    
    # ดึงการจองโดยใช้ username ของผู้ใช้ปัจจุบัน
    user_reservations = Reservation.objects.filter(
        customer_name=request.user.username
    ).order_by('-reservation_date', 'start_time')
    
    context = {
        'loggedin': logged_in['loggedin'],
        'user': logged_in['user'],
        'reservations': user_reservations,
    }
    
    return render(request, 'public/my-reservations.html', context)

# Register view
def RegisterView(request):
    if request.method == "POST":
        # Get username, email, and password from POST request
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')
        confirm_password = request.POST.get('confirm_password')
        user_data_has_error = False

        if not user_data_has_error:
             # Create new user
             new_user = CustomerUsers.objects.create_user(
                 email=email,
                 username=username,
                 password=password,
                 phone_number=phone_number
             )
        # errors = {}
        # # Check if username or email already exists
        # if CustomerUsers.objects.filter(username=username).exists():
        #     user_data_has_error = True
        #     #messages.error(request, "ชื่อผู้ใช้นี้มีอยู่แล้ว")
        #     errors['username'] = "ชื่อผู้ใช้นี้มีอยู่แล้ว"
        # if CustomerUsers.objects.filter(email=email).exists():
        #     user_data_has_error = True
        #     #messages.error(request, "อีเมลนี้มีอยู่แล้ว")
        #     errors['email'] = "ชื่อผู้ใช้นี้มีอยู่แล้ว"
        # if len(password) < 5:
        #     user_data_has_error = True
        #     #messages.error(request, "รหัสผ่านต้องมีอย่างน้อย 5 ตัวอักษร")
        #     errors['password'] = "รหัสผ่านต้องมีอย่างน้อย 5 ตัวอักษร"
        # if len(phone_number) != 10:
        #     user_data_has_error = True
        #    #messages.error(request, "หมายเลขโทรศัพท์ต้องมี 10 หลัก")
        #     errors['phone_number'] = "โปรดกรอกหมายเลขโทรศัพทที่ถูกต้อง"
        # if password != confirm_password:
        #     user_data_has_error = True
        #     #messages.error(request, "รหัสผ่านไม่ตรงกัน")
        #     errors['confirm_password'] = "รหัสผ่านไม่ตรงกัน"
        # if user_data_has_error:
        #     return redirect(request, 'register-th', {'errors': errors})
        # else:
        #     # Create new user
        #     new_user = CustomerUsers.objects.create_user(
        #         email=email,
        #         username=username,
        #         password=password,
        #         phone_number=phone_number
        #     )

        messages.success(request, "สร้างบัญชีเรียบร้อยแล้ว")

    return render(request, 'public/register-th.html')

# Logout view
@login_required
def LogoutView(request):
    if request.user != None:
        logout(request)
    return redirect('/')

# admin page

def isSuperUser(request):
    logged_in = check_login(request)
    if not logged_in['loggedin']:
        return redirect('login-th')
    if not logged_in['user'].is_superuser:
        return HttpResponseForbidden("You do not have permission to access this page.")  # 403 Forbidden
    return logged_in

def admin_dashboard(request):
    reservation = Reservation.objects.all()
    logged_in = isSuperUser(request)
    # Handle cases where `isSuperUser` returns a response (redirect or forbidden)
    if isinstance(logged_in, (HttpResponseForbidden, HttpResponseRedirect)):
        return logged_in  # Return the response immediately
    
    user_count = User.objects.count()  # Get all users
    reservation_count = Reservation.objects.count()
    pending_count = Reservation.objects.filter(status='pending').count()

    context = {
        'logged_in': logged_in['loggedin'],
        'user': logged_in['user'],
        'user_count': user_count,  # Pass users to the template
        'reservation': reservation,
        'reservation_count': reservation_count,
        'pending_count': pending_count,
    }
    return render(request, 'private/dashboard.html', context)

def  admin_userManagement(request):
    logged_in = isSuperUser(request)
    # Handle cases where `isSuperUser` returns a response (redirect or forbidden)
    if isinstance(logged_in, (HttpResponseForbidden, HttpResponseRedirect)):
        return logged_in  # Return the response immediately
    
    users = User.objects.all()  # Get all users

    context = {
        'logged_in': logged_in['loggedin'],
        'user': logged_in['user'],
        'users': users,  # Pass users to the template
        'field_sizes': ['Small', 'Medium', 'Large'],
    }

    return render(request, 'private/userManagement.html', context)

def admin_reservaionManagement(request):
    reservations = Reservation.objects.all()
    logged_in = isSuperUser(request)
    # Handle cases where `isSuperUser` returns a response (redirect or forbidden)
    if isinstance(logged_in, (HttpResponseForbidden, HttpResponseRedirect)):
        return logged_in  # Return the response immediately
    
    user_count = User.objects.count()  # Get all users

    context = {
        'logged_in': logged_in['loggedin'],
        'user': logged_in['user'],
        'user_count': user_count,  # Pass users to the template
        'reservation': reservations
    }
    return render(request, 'private/reservationManagement.html', context)
# Reserve view with login required
def PrereserveView(request):
    logged_in = check_login(request)
    return render(request, 'public/resevation/pre-reservation.html', logged_in)

def ReserveView(request):
    logged_in = check_login(request)
    return render(request, 'public/resevation/reservation.html', logged_in)

def BigReserveView(request):  # for big
    logged_in = check_login(request)
    return render(request, 'public/resevation/big-reservation.html', logged_in)

def MediumReserveView(request):  # for medium
    logged_in = check_login(request)
    return render(request, 'public/resevation/medium-reservation.html', logged_in)

def SmallReserveView(request):  # for small
    logged_in = check_login(request)
    return render(request, 'public/resevation/small-reservation.html', logged_in)

# About us
def AboutusView(request):
    logged_in = check_login(request)
    return render(request, 'public/aboutus.html', logged_in)

User = get_user_model()
# User Edit ------temporary-----
def UserEditView(request):
    logged_in = check_login(request)
    return render(request, 'public/edit-user.html', logged_in)


# Forgot password view with GET and POST methods allowed
@csrf_protect
def ForgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            # Create PasswordReset object to reset password
            user = CustomerUsers.objects.get(email=email)
            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()

            # Generate password reset URL
            password_reset_url = reverse('reset-password', kwargs={'reset_id': new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            # Email body with reset link
            email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'

            # Create email message
            email_message = EmailMessage(
                'Reset your password',  # Email subject
                email_body,
                settings.EMAIL_HOST_USER,  # Email sender
                [email]  # Receiver email
            )
            # Set email priority headers
            email_message.extra_headers = {
                'X-Priority': '1',
                'X-MSMail-Priority': 'High',
                'Importance': 'High',
                'Priority': 'urgent'
            }
            # Continue without crashing web if sending email has an error
            email_message.fail_silently = True

            # Send email
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except CustomerUsers.DoesNotExist:
            messages.error(request, "ไม่พบอีเมลนี้")
            return redirect('forgot-password')

    return render(request, 'public/passwordRecovery/forgot_password.html')

# Password reset sent view
def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'public/passwordRecovery/password_reset_sent.html')
    else:
        # Redirect if reset id is invalid
        messages.error(request, "ลิงก์รีเซ็ตรหัสผ่านไม่ถูกต้อง")
        return redirect('forgot-password')

# Password reset sent ---for testing---
def PasswordResetSentForTesting(request):
    return render(request, 'public/passwordRecovery/password_reset_sent.html')

# Reset password view
def ResetPassword(request, reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)
        if request.method == "POST":
            # Get password and confirm_password from POST request
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            passwords_have_error = False

            # Check if passwords match
            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, "รหัสผ่านไม่ตรงกัน")

            # Check if password length is sufficient
            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'รหัสผ่านต้องมีอย่างน้อย 5 ตัวอักษร')

            # Check if reset link has expired
            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)
            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, "ลิงก์รีเซ็ตรหัสผ่านหมดอายุแล้ว")
                password_reset_id.delete()

            if not passwords_have_error:
                # Set new password for user
                user = password_reset_id.user
                user.set_password(password)
                user.save()

                # Delete password reset object
                password_reset_id.delete()

                messages.success(request, "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")
                return redirect('login-th')
            else:
                # Redirect back to password reset page and display errors
                return redirect('reset-password', reset_id=reset_id)
    # Send error and return back to forgot password page
    except PasswordReset.DoesNotExist:
        logger.warning(f"Invalid password reset attempt with reset_id: {reset_id}")
        messages.error(request, "ลิงก์รีเซ็ตรหัสผ่านไม่ถูกต้อง")
        return redirect('forgot-password')

    return render(request, 'public/passwordRecovery/reset_password.html')

#image and gallery 
def gallery_view(request):
    logged_in = check_login(request)
    return render(request, "public/gallery.html", logged_in)

def admin_gallery(request):
    logged_in = check_login(request)
    return render(request, "private/galleryManagement.html", logged_in)

def contactUsView(request):
    logged_in = check_login(request)
    return render(request, "public/contactus.html", logged_in)

def guideView(request):
    logged_in = check_login(request)
    return render(request, "public/guide.html" , logged_in)