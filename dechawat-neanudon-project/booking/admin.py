from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Field, Reservation

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
            status='booked'
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
                   'start_time', 'end_time', 'status', 'total_price')
    list_filter = ('status', 'reservation_date', 'field')
    search_fields = ('customer_name', 'phone')
    date_hierarchy = 'reservation_date'
    
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

    def has_delete_permission(self, request, obj=None):
        return False

# สร้าง Custom Admin Site instance
admin_site = CustomAdminSite(name='custom_admin')
admin_site.register(Field, FieldAdmin)
admin_site.register(Reservation, ReservationAdmin)