from django.shortcuts import render
from django.http import JsonResponse
from .models import Field, Reservation
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

def check_login(request):
    return {
        'loggedin': request.user.is_authenticated,
        'user': request.user
    }

@api_view(['GET'])
@permission_classes([AllowAny])
def get_fields(request):
    field_id = request.GET.get('id')
    if field_id:
        fields = Field.objects.filter(id=field_id)
    else:
        fields = Field.objects.all()
        
    return Response([{
        'id': field.id,
        'name': field.name,
        'capacity': field.capacity,
        'price_per_hour': float(field.price_per_hour)
    } for field in fields])

@api_view(['GET'])
@permission_classes([AllowAny])
def check_availability(request):
    date_str = request.GET.get('date')
    field_id = request.GET.get('field_id')
    
    if not date_str or not field_id:
        return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all reservations for the selected date and field
        reservations = Reservation.objects.filter(
            field_id=field_id,
            reservation_date=date,
            status='booked'
        )

        # Create time slots (14:00 - 23:00)
        time_slots = []
        for hour in range(14, 24):  # Stop at 23
            start_time = f"{hour:02d}:00"
            end_time = f"{(hour + 1) % 24:02d}:00"  # Use modulo for midnight
            
            # แปลงเวลาเป็น time objects
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            
            # Check if this time slot is reserved
            is_reserved = reservations.filter(
                start_time__lte=end_time_obj,
                end_time__gt=start_time_obj
            ).exists()
            
            time_slots.append({
                'start': f"{hour:02d}.00",
                'end': f"{(hour + 1) % 24:02d}.00",
                'status': 'reserved' if is_reserved else 'available'
            })
        
        print(f"Time slots for {date}: {time_slots}")  # Debug print
        return Response({'time_slots': time_slots})
        
    except Exception as e:
        print(f"Error in check_availability: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def create_reservation(request):
    try:
        data = request.data
        print("Received data:", data)  # Debug print
        
        field = Field.objects.get(id=data['field_id'])
        
        # แปลงรูปแบบเวลาจาก "14.00" เป็น "14:00"
        start_time_str = data['start_time'].replace('.', ':')
        end_time_str = data['end_time'].replace('.', ':')
        
        # แปลงเป็น time objects
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        reservation_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

        # ตรวจสอบว่าช่วงเวลานี้ว่างหรือไม่
        existing_reservation = Reservation.objects.filter(
            field=field,
            reservation_date=reservation_date,
            status='booked'
        ).filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()
        
        if existing_reservation:
            return Response({
                'status': 'error',
                'message': 'ช่วงเวลานี้มีการจองแล้ว กรุณาเลือกเวลาอื่น'
            }, status=status.HTTP_400_BAD_REQUEST)

        # สร้างการจอง
        reservation = Reservation.objects.create(
            field=field,
            reservation_date=reservation_date,
            start_time=start_time,
            end_time=end_time,
            customer_name=data['customer_name'],
            phone=data['phone'],
            total_price=Decimal(str(data['total_price'])),
            status='booked'
        )
        
        return Response({
            'status': 'success',
            'reservation_id': reservation.id
        })
        
    except Field.DoesNotExist:
        return Response({
            'status': 'error',
            'message': f"ไม่พบสนามหมายเลข {data.get('field_id')}"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
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