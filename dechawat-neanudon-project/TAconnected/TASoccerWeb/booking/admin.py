from pyexpat.errors import messages
from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponseRedirect
from datetime import datetime, timedelta
from .models import *
from Useraccounts.models import CustomerUsers 
from LoginSystem.models import PasswordReset

# Custom Admin Site Class
class CustomAdminSite(admin.AdminSite):
    site_header = 'T.A.SOCCER Admin'
    site_title = 'T.A.SOCCER Admin Portal'
    index_title = 'ระบบจัดการสนามฟุตบอล'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard-stats/', self.admin_view(self.dashboard_stats), 
                 name='dashboard-stats'),
        ]
        return custom_urls + urls

    def dashboard_stats(self, request):
        today = datetime.now().date()
        today_bookings = Reservation.objects.filter(
            reservation_date=today
        ).count()
        
        # จำนวนการจองที่รอการยืนยัน
        pending_bookings = Reservation.objects.filter(
            status='pending'
        ).count()

        this_month = datetime.now().replace(day=1).date()
        monthly_revenue = Reservation.objects.filter(
            reservation_date__gte=this_month,
            status='booked'  # เฉพาะการจองที่ยืนยันแล้วเท่านั้น
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0

        return JsonResponse({
            'today_bookings': today_bookings,
            'pending_bookings': pending_bookings,
            'monthly_revenue': float(monthly_revenue)
        })

# Admin Model Classes
@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'price_per_hour')
    search_fields = ('name',)
    list_filter = ('capacity',)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'field', 'reservation_date', 
                   'start_time', 'end_time', 'status_colored', 'total_price', 'action_buttons')
    list_filter = ('status', 'reservation_date', 'field')
    search_fields = ('customer_name', 'phone')
    date_hierarchy = 'reservation_date'
    actions = ['confirm_bookings', 'cancel_bookings']
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('ข้อมูลการจอง', {
            'fields': ('field', 'reservation_date', 'start_time', 'end_time')
        }),
        ('ข้อมูลลูกค้า', {
            'fields': ('customer_name', 'phone')
        }),
        ('รายละเอียดการชำระเงิน', {
            'fields': ('total_price', 'status')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'booked': 'green',
            'cancelled': 'red',
        }
        status_display = obj.get_status_display()
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, status_display)
    
    status_colored.short_description = 'สถานะ'
    
    def action_buttons(self, obj):
        """แสดงปุ่มการกระทำตามสถานะ"""
        if obj.status == 'pending':
            confirm_url = reverse('admin:confirm_reservation', args=[obj.pk])
            cancel_url = reverse('admin:cancel_reservation', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">ยืนยัน</a> '
                '<a class="button" href="{}">ยกเลิก</a>',
                confirm_url, cancel_url
            )
        return ''
    
    action_buttons.short_description = 'ยืนยัน'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'confirm-reservation/<int:reservation_id>/',
                self.admin_site.admin_view(self.confirm_reservation),
                name='confirm_reservation',
            ),
            path(
                'cancel-reservation/<int:reservation_id>/',
                self.admin_site.admin_view(self.cancel_reservation),
                name='cancel_reservation',
            ),
        ]
        return custom_urls + urls
    
    def confirm_reservation(self, request, reservation_id):
        """ยืนยันการจองจากหน้า admin"""
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.status = 'booked'
            reservation.save()
            messages.success(request, f'ยืนยันการจองสำเร็จ: {reservation}')
        except Reservation.DoesNotExist:
            messages.error(request, 'ไม่พบการจองที่ระบุ')
        return HttpResponseRedirect(reverse('admin:booking_reservation_changelist'))

    def cancel_reservation(self, request, reservation_id):
            """ยกเลิกการจองจากหน้า admin"""
            try:
                reservation = Reservation.objects.get(id=reservation_id)
                reservation.status = 'cancelled'
                reservation.save()
                messages.success(request, f'ยกเลิกการจองสำเร็จ: {reservation}')
            except Reservation.DoesNotExist:
                messages.error(request, 'ไม่พบการจองที่ระบุ')
            return HttpResponseRedirect(reverse('admin:booking_reservation_changelist'))
    
    def confirm_bookings(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='booked')
        self.message_user(request, f'ยืนยันการจองสำเร็จ {updated} รายการ')
    confirm_bookings.short_description = "ยืนยันการจองที่เลือก"
    
    def cancel_bookings(self, request, queryset):
        updated = queryset.exclude(status='cancelled').update(status='cancelled')
        self.message_user(request, f'ยกเลิกการจองสำเร็จ {updated} รายการ')
    cancel_bookings.short_description = "ยกเลิกการจองที่เลือก"

    def has_delete_permission(self, request, obj=None):
        return False

# สร้าง Custom Admin Site instance
admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(Field, FieldAdmin)
admin_site.register(Reservation, ReservationAdmin)
admin_site.register(CustomerUsers)
admin_site.register(PasswordReset)