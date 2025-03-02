# Create your models here.
from django.db import models

class Field(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()  # เพิ่ม field capacity
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} (สำหรับ {self.capacity} คน)"

class Reservation(models.Model):  # เปลี่ยนจาก Booking เป็น Reservation
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    reservation_date = models.DateField()  # เปลี่ยนจาก booking_date
    start_time = models.TimeField()
    end_time = models.TimeField()
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='booked')  # เปลี่ยนจาก booking_status
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # เพิ่ม field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field.name} - {self.reservation_date} ({self.start_time}-{self.end_time})"