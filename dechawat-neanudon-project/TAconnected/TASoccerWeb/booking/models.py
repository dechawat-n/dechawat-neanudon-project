from django.db import models

class Field(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.name} (สำหรับ {self.capacity} คน)"

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'กำลังจอง'),  # สถานะใหม่เพื่อรอการยืนยันจาก admin
        ('booked', 'จองแล้ว'),
        ('cancelled', 'ยกเลิก'),
    )
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # เปลี่ยนจาก default='booked' เป็น 'pending'
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field.name} - {self.reservation_date} ({self.start_time}-{self.end_time}) - {self.get_status_display()}"