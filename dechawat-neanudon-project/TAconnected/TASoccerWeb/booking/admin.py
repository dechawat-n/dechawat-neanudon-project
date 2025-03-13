from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import JsonResponse
from django.shortcuts import redirect, render
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

        this_month = datetime.now().replace(day=1).date()
        monthly_revenue = Reservation.objects.filter(
            reservation_date__gte=this_month,
            status='confirmed'
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0

        return JsonResponse({
            'today_bookings': today_bookings,
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
                   'start_time', 'end_time', 'status', 'total_price', 'reservation_actions')
    list_filter = ('status', 'reservation_date', 'field')
    search_fields = ('customer_name', 'phone')
    date_hierarchy = 'reservation_date'
    
    readonly_fields = ('created_at', 'time_slots_display')
    
    fieldsets = (
        ('ข้อมูลการจอง', {
            'fields': ('field', 'reservation_date', 'start_time', 'end_time', 'time_slots_display')
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
    
    def time_slots_display(self, obj):
        if not obj.time_slots_data:
            return '-'
        
        slots = []
        for slot in obj.time_slots_data:
            slots.append(f"{slot['start']} - {slot['end']}")
        
        return format_html("<br>".join(slots))
    
    time_slots_display.short_description = "รายละเอียดช่วงเวลา"

    def reservation_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a class="button" href="{}">ยืนยัน</a> | <a class="button" href="{}">ยกเลิก</a>',
                reverse('admin:confirm_reservation', args=[obj.pk]),
                reverse('admin:cancel_reservation', args=[obj.pk])
            )
        elif obj.status == 'confirmed':
            return format_html(
                '<a class="button" href="{}">ยกเลิก</a>',
                reverse('admin:cancel_reservation', args=[obj.pk])
            )
        return '-'
    
    reservation_actions.short_description = 'การดำเนินการ'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'confirm/<int:reservation_id>/',
                self.admin_site.admin_view(self.confirm_reservation),
                name='confirm_reservation',
            ),
            path(
                'cancel/<int:reservation_id>/',
                self.admin_site.admin_view(self.cancel_reservation),
                name='cancel_reservation',
            ),
            path(
                'fields-management/',
                self.admin_site.admin_view(self.fields_management_view),
                name='fields_management',
            ),
        ]
        return custom_urls + urls
    
    def confirm_reservation(self, request, reservation_id):
        reservation = self.get_queryset(request).get(pk=reservation_id)
        reservation.status = 'confirmed'
        reservation.save()
        self.message_user(request, f'ยืนยันการจองของ {reservation.customer_name} สำเร็จ')
        return redirect('admin:booking_reservation_changelist')
    
    def cancel_reservation(self, request, reservation_id):
        reservation = self.get_queryset(request).get(pk=reservation_id)
        reservation.status = 'cancelled'
        reservation.save()
        self.message_user(request, f'ยกเลิกการจองของ {reservation.customer_name} สำเร็จ')
        return redirect('admin:booking_reservation_changelist')
    
    def fields_management_view(self, request):
        from .models import Field
        context = {
            'title': 'จัดการสนาม',
            'app_label': 'booking',
            'opts': Field._meta,
            'fields': Field.objects.all(),
        }
        return render(request, 'admin/booking/fields_management.html', context)

    def has_delete_permission(self, request, obj=None):
        return False

# Create a Field Management view
class FieldManagementAdmin(admin.ModelAdmin):
    change_list_template = 'admin/field_management_change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['fields'] = Field.objects.all()
        return super().changelist_view(request, extra_context=extra_context)

# สร้าง Custom Admin Site instance
admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(Field, FieldAdmin)
admin_site.register(Reservation, ReservationAdmin)
admin_site.register(CustomerUsers)
admin_site.register(PasswordReset)