from django.shortcuts import render
from django.http import JsonResponse
from .models import Field, Reservation
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
import os
from decimal import Decimal

def get_fields(request):
    fields = Field.objects.all()
    return JsonResponse([{
        'id': field.id,
        'name': field.name,
        'capacity': field.capacity,
        'price_per_hour': float(field.price_per_hour)
    } for field in fields], safe=False)

@csrf_exempt
def check_availability(request):
    date_str = request.GET.get('date')
    field_id = request.GET.get('field_id')
    
    if not date_str or not field_id:
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    try:
        # แปลงวันที่
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # ดึงการจองทั้งหมดของวันที่เลือก
        reservations = Reservation.objects.filter(
            field_id=field_id,
            reservation_date=date,
            status='booked'
        )
        
        # สร้างช่วงเวลาทั้งหมด (7:00-24:00)
        time_slots = []
        for hour in range(7, 24):
            start = datetime.strptime(f"{hour}:00", "%H:%M").time()
            end = datetime.strptime(f"{hour + 1}:00", "%H:%M").time()
            
            # เช็คว่าช่วงเวลานี้มีการจองหรือไม่
            is_booked = reservations.filter(
                start_time__lt=end,
                end_time__gt=start
            ).exists()
            
            time_slots.append({
                'start': start.strftime('%H:%M'),
                'end': end.strftime('%H:%M'),
                'status': 'reserved' if is_booked else 'available'
            })
        
        return JsonResponse({'time_slots': time_slots})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def create_reservation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        field = Field.objects.get(id=data['field_id'])
        
        # แปลงเวลาเริ่มและสิ้นสุด
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        
        # คำนวณราคารวม
        hours = ((datetime.combine(datetime.min, end_time) - 
                 datetime.combine(datetime.min, start_time)).seconds / 3600)
        total_price = field.price_per_hour * hours
        
        # สร้างการจอง
        reservation = Reservation.objects.create(
            field=field,
            reservation_date=data['date'],
            start_time=start_time,
            end_time=end_time,
            customer_name=data['customer_name'],
            phone=data['phone'],
            total_price=total_price,
            status='booked'
        )
        
        return JsonResponse({
            'status': 'success',
            'reservation_id': reservation.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def home_view(request):
    return render(request, 'home-th.html')

def reservation_view(request):
    return render(request, 'reservation/reservation.html')