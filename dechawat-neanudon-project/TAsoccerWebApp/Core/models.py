from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid
from django.utils import timezone

class CustomerUsers(AbstractUser):
    phone_number = models.CharField(max_length=10, blank=True, null=True)

    # Remove the Meta class entirely or remove db_table setting
    def __str__(self):
        return f" {self.username}"

class PasswordReset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    
class Reservation(models.Model):
    customer_name = models.CharField(max_length=255)
    field = models.CharField(max_length=100)  # Example: "Field A"
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    contact_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("confirmed", "Confirmed")], default="pending")

    def __str__(self):
        return f"{self.customer_name} - {self.field} on {self.date}"