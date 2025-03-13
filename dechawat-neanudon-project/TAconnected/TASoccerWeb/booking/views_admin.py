from django.shortcuts import render
from .models import Field

def fields_management_view(request):
    fields = Field.objects.all()
    context = {
        'title': 'จัดการสนาม',
        'fields': fields
    }
    return render(request, 'admin/booking/fields_management.html', context)