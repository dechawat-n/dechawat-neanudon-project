from django.shortcuts import render
from django.http import JsonResponse
from .models import Field, Reservation
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

def check_login(request):
    return {
        'loggedin': request.user.is_authenticated,
        'user': request.user
    }

@api_view(['GET'])
@permission_classes([AllowAny])
def get_fields(request):
    field_id = request.GET.get('id')
    if field_id:
        fields = Field.objects.filter(id=field_id)
    else:
        fields = Field.objects.all()
        
    return Response([{
        'id': field.id,
        'name': field.name,
        'capacity': field.capacity,
        'price_per_hour': float(field.price_per_hour)
    } for field in fields])

@api_view(['GET'])
@permission_classes([AllowAny])
def check_availability(request):
    date_str = request.GET.get('date')
    field_id = request.GET.get('field_id')
    
    if not date_str or not field_id:
        return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        next_day = date + timedelta(days=1)
        
        # แยกการค้นหาเป็นสองส่วน: confirmed และ pending
        confirmed_reservations = Reservation.objects.filter(
            field_id=field_id,
            reservation_date=date,
            status='confirmed'  # เฉพาะที่ยืนยันแล้ว
        )
        
        pending_reservations = Reservation.objects.filter(
            field_id=field_id,
            reservation_date=date,
            status='pending'  # เฉพาะที่รอยืนยัน
        )

        # สำหรับช่วงเวลา 23:00-00:00 ที่อาจข้ามวัน
        next_day_reservations = Reservation.objects.filter(
            field_id=field_id,
            reservation_date=next_day,
            start_time=datetime.strptime('00:00', '%H:%M').time(),
            status__in=['confirmed', 'pending']
        )
        
        # สร้างช่วงเวลา (14:00 - 24:00)
        time_slots = []
        for hour in range(14, 24):
            start_time = f"{hour:02d}:00"
            
            # จัดการกับช่วงเวลา 23:00-24:00 เป็นพิเศษ
            if hour == 23:
                end_time = "00:00"
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                # ตรวจสอบว่าช่วงเวลานี้มีการจองหรือไม่
                is_confirmed = confirmed_reservations.filter(
                    start_time__lte=datetime.strptime(start_time, '%H:%M').time(),
                    end_time__gte=datetime.strptime(start_time, '%H:%M').time()
                ).exists() or next_day_reservations.filter(status='confirmed').exists()
                
                is_pending = pending_reservations.filter(
                    start_time__lte=datetime.strptime(start_time, '%H:%M').time(),
                    end_time__gte=datetime.strptime(start_time, '%H:%M').time()
                ).exists() or next_day_reservations.filter(status='pending').exists()
            else:
                end_time = f"{(hour + 1):02d}:00"
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                
                # ตรวจสอบว่าช่วงเวลานี้มีการจองหรือไม่
                is_confirmed = confirmed_reservations.filter(
                    start_time__lte=datetime.strptime(end_time, '%H:%M').time(),
                    end_time__gt=datetime.strptime(start_time, '%H:%M').time()
                ).exists()
                
                is_pending = pending_reservations.filter(
                    start_time__lte=datetime.strptime(end_time, '%H:%M').time(),
                    end_time__gt=datetime.strptime(start_time, '%H:%M').time()
                ).exists()
            
            # กำหนดสถานะของช่วงเวลา
            if is_confirmed:
                status_val = 'confirmed'
            elif is_pending:
                status_val = 'pending'
            else:
                status_val = 'available'
                
            time_slots.append({
                'start': f"{hour:02d}.00",
                'end': "00.00" if hour == 23 else f"{(hour + 1):02d}.00",
                'status': status_val
            })
        
        print(f"Time slots for {date}: {time_slots}")  # Debug print
        return Response({'time_slots': time_slots})
        
    except Exception as e:
        print(f"Error in check_availability: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def create_reservation(request):
    if not request.user.is_authenticated:
        return Response({
            'status': 'error',
            'message': 'กรุณาเข้าสู่ระบบก่อนทำการจอง'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        data = request.data
        print("Received data:", data)  # Debug print
        
        field = Field.objects.get(id=data['field_id'])
        
        # Format times properly
        start_time_str = data['start_time'].replace('.', ':')
        end_time_str = data['end_time'].replace('.', ':')
        
        # Special handling for midnight
        if end_time_str == '24:00':
            end_time_str = '00:00'
        
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        reservation_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

        # Check if the slot is available
        existing_reservation = Reservation.objects.filter(
            field=field,
            reservation_date=reservation_date,
            status__in=['confirmed', 'pending']
        ).filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        
        if existing_reservation:
            return Response({
                'status': 'error',
                'message': 'ช่วงเวลานี้มีการจองแล้ว กรุณาเลือกเวลาอื่น'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Store detailed time slots
        time_slots = []
        if 'time_slots' in data and data['time_slots']:
            time_slots = data['time_slots']
        
        # Create the reservation with pending status
        reservation = Reservation.objects.create(
            field=field,
            reservation_date=reservation_date,
            start_time=start_time,
            end_time=end_time,
            customer_name=data['customer_name'],
            phone=data['phone'],
            total_price=Decimal(str(data['total_price'])),
            status='pending',  # Set status to pending by default
            time_slots_data=time_slots
        )
        
        return Response({
            'status': 'success',
            'reservation_id': reservation.id
        })
        
    except Field.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f"ไม่พบสนามหมายเลข {data.get('field_id')}"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
def home_view(request):
    return render(request, 'home-th.html')

def pre_reservation_view(request):
    logged_in = check_login(request)
    return render(request, 'public/resevation/pre-reservation.html', logged_in)
    
def reservation_view(request):
    field_id = request.GET.get('field_id')
    if field_id:
        field = Field.objects.get(id=field_id)
        return render(request, 'reservation.html', {'field': field})
    return render(request, 'reservation.html')

def ReserveView(request):
    logged_in = check_login(request)
    return render(request, 'public/resevation/reservation.html', logged_in)

def BigReserveView(request):  
    context = check_login(request)  
    return render(request, 'public/resevation/big-reservation.html', context)

def MediumReserveView(request):  
    context = check_login(request)  
    return render(request, 'public/resevation/medium-reservation.html', context)

def SmallReserveView(request):  
    context = check_login(request)  
    return render(request, 'public/resevation/small-reservation.html', context)