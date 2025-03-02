from django.contrib import admin
from .models import *
from Useraccounts.models import CustomerUsers
#make password reset data visible to admin panel
admin.site.register(PasswordReset)
admin.site.register(CustomerUsers)

# Register your models here.
