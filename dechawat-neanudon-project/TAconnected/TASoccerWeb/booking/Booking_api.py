from django.shortcuts import render
from django.http import JsonResponse
from .models import Field, Reservation
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required

def check_login(request):
    return {
        'loggedin': request.user.is_authenticated,
        'user': request.user
    }
    
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

def BigReserveView(request):  # for big
    logged_in = check_login(request)
    return render(request, 'public/resevation/big-reservation.html', logged_in)

def MediumReserveView(request):  # for medium
    logged_in = check_login(request)
    return render(request, 'public/resevation/medium-reservation.html', logged_in)

def SmallReserveView(request):  # for small
    logged_in = check_login(request)
    return render(request, 'public/resevation/small-reservation.html', logged_in)