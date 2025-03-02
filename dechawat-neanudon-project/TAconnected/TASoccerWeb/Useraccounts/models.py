from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomerUsers(AbstractUser):
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customer_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customer_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    class Meta:
        verbose_name = 'Customer User'
        verbose_name_plural = 'Customer Users'

    def __str__(self):
        return f" {self.username}"