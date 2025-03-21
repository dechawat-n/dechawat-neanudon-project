from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.decorators import api_view, action
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta

from .models import Field, Reservation
from .serializers import FieldSerializer, ReservationSerializer, ReservationConfirmSerializer

class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    
    # อนุญาตให้ Admin เท่านั้นที่สามารถเพิ่ม/แก้ไข/ลบ สนามได้
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by('-created_at')
    serializer_class = ReservationSerializer

    def get_permissions(self):
        if self.action in ['confirm', 'cancel']:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action in ['confirm', 'cancel']:
            return ReservationConfirmSerializer
        return self.serializer_class
    
    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
            """API endpoint สำหรับยืนยันการจองโดย admin"""
            try:
                # ดึงข้อมูลการจอง
                reservation = self.get_object()
                
                # เปลี่ยนสถานะเป็นจอง
                reservation.status = 'booked'
                reservation.save()
                
                # ใช้ serializer สำหรับ confirm
                serializer = self.get_serializer(reservation, data={'status': 'booked'}, partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': 'success', 
                        'reservation': serializer.data
                    })
                else:
                    return Response({
                        'status': 'error', 
                        'message': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({
                    'status': 'error', 
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
            """API endpoint สำหรับยกเลิกการจองโดย admin"""
            try:
                # ดึงข้อมูลการจอง
                reservation = self.get_object()
                
                # เปลี่ยนสถานะเป็นยกเลิก
                reservation.status = 'cancelled'
                reservation.save()
                
                # ใช้ serializer สำหรับ cancel
                serializer = self.get_serializer(reservation, data={'status': 'cancelled'}, partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'status': 'success', 
                        'reservation': serializer.data
                    })
                else:
                    return Response({
                        'status': 'error', 
                        'message': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({
                    'status': 'error', 
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
            """API endpoint สำหรับอัปเดตสถานะการจองโดย admin"""
            try:
                reservation = self.get_object()
                new_status = request.data.get('status')
                
                if new_status not in dict(Reservation.STATUS_CHOICES):
                    return Response({
                        'status': 'error', 
                        'message': 'สถานะไม่ถูกต้อง'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                reservation.status = new_status
                reservation.save()
                
                serializer = self.get_serializer(reservation)
                return Response({
                    'status': 'success', 
                    'reservation': serializer.data
                })
            
            except Exception as e:
                return Response({
                    'status': 'error', 
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def check_availability(request):
    """
    ตรวจสอบเวลาที่ว่างสำหรับสนามที่เลือก
    """
    date_str = request.GET.get('date')
    field_id = request.GET.get('field_id')
    
    if not date_str or not field_id:
        return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # แสดง log เพื่อการตรวจสอบ
        print(f"Checking availability for field_id={field_id}, date={date}")
        
        # ดึงข้อมูลการจองทั้งหมดที่มีสถานะเป็น 'pending' หรือ 'booked'
        reservations = Reservation.objects.filter(
            field_id=field_id,
            reservation_date=date,
            status__in=['pending', 'booked']  # ครอบคลุมทั้งสถานะรอและจองแล้ว
        )
        
        # แสดงข้อมูลการจองที่พบ
        for res in reservations:
            print(f"Found reservation: ID={res.id}, {res.start_time}-{res.end_time}, status={res.status}, customer={res.customer_name}")
        
        # สร้าง time slots ทั้งหมด (14:00 - 23:00)
        time_slots = []
        for hour in range(14, 24):
            start_time = f"{hour:02d}:00"
            end_time = f"{(hour + 1) % 24:02d}:00"
            
            # แปลงเวลาเป็น time objects
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time() if hour < 23 else datetime.strptime("00:00", '%H:%M').time()
            
            print(f"Checking slot: {start_time}-{end_time}")
            
            # เปลี่ยนวิธีการตรวจสอบการซ้อนทับของเวลา
            slot_reserved = False
            slot_pending = False
            
            for res in reservations:
                res_start = res.start_time
                res_end = res.end_time
                
                # กรณีพิเศษสำหรับการจัดการเวลาที่ข้ามวัน
                if res_end.hour == 0 and res_end.minute == 0:  # เวลาสิ้นสุดคือเที่ยงคืน
                    # ตรวจสอบว่าช่วงเวลาปัจจุบันอยู่ก่อนเที่ยงคืนหรือไม่ (คือตั้งแต่เวลาเริ่มต้นจนถึงเที่ยงคืน)
                    if start_time_obj >= res_start:
                        print(f"  Special midnight case: This slot is between {res_start} and midnight")
                        if res.status == 'booked':
                            slot_reserved = True
                        elif res.status == 'pending':
                            slot_pending = True
                    continue
                
                # การตรวจสอบปกติ (ดูว่าช่วงเวลาที่กำลังตรวจสอบทับซ้อนกับการจองหรือไม่)
                is_overlap = False
                
                # กรณีที่ 1: เวลาเริ่มต้นของช่วงเวลาอยู่ระหว่างการจอง
                if res_start <= start_time_obj < res_end:
                    is_overlap = True
                
                # กรณีที่ 2: เวลาสิ้นสุดของช่วงเวลาอยู่ระหว่างการจอง
                elif res_start < end_time_obj <= res_end:
                    is_overlap = True
                    
                # กรณีที่ 3: ช่วงเวลาครอบคลุมการจองทั้งหมด
                elif start_time_obj <= res_start and end_time_obj >= res_end:
                    is_overlap = True
                
                # กรณีพิเศษสำหรับเวลาข้ามวัน
                if end_time_obj.hour == 0 and res_end.hour == 0:
                    # ถ้าทั้งคู่จบที่เที่ยงคืน ให้ตรวจสอบว่าเวลาเริ่มต้นทับซ้อนกัน
                    if start_time_obj >= res_start or res_start >= start_time_obj:
                        is_overlap = True
                
                if is_overlap:
                    print(f"  Overlap with reservation {res.id}: {res_start}-{res_end}, status={res.status}")
                    if res.status == 'booked':
                        slot_reserved = True
                    elif res.status == 'pending':
                        slot_pending = True
            
            # กำหนดสถานะ
            if slot_reserved:
                status_val = 'booked'
            elif slot_pending:
                status_val = 'pending'
            else:
                status_val = 'available'
            
            time_slots.append({
                'start': f"{hour:02d}.00",
                'end': f"{(hour + 1) % 24:02d}.00",
                'status': status_val
            })
        
        print(f"Final time slots: {[f'{slot['start']}-{slot['end']}: {slot['status']}' for slot in time_slots]}")
        return Response({'time_slots': time_slots})
        
    except Exception as e:
        print(f"Error in check_availability: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
def create_reservation(request):
    """
    สร้างการจองใหม่
    """
    try:
        # ถ้าผู้ใช้ล็อกอิน ให้ใช้ชื่อผู้ใช้เป็นชื่อผู้จอง
        if request.user.is_authenticated:
            request.data['customer_name'] = request.user.username

        # แสดงข้อมูลที่ได้รับเพื่อการแก้ไขข้อผิดพลาด
        print("Received data:", request.data)
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['field', 'reservation_date', 'start_time', 'end_time', 
                          'customer_name', 'phone', 'total_price']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'status': 'error',
                    'message': f'ข้อมูล {field} ไม่ถูกส่งมา'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # แปลงข้อมูล
        data = request.data.copy()
        
        # กรณีพิเศษสำหรับเวลาสิ้นสุด 00:00
        if data['end_time'] == '00:00':
            print("Special case: End time is 00:00")
        elif data['start_time'] >= data['end_time']:
            return Response({
                'status': 'error',
                'message': 'เวลาเริ่มต้นต้องน้อยกว่าเวลาสิ้นสุด'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ตรวจสอบสนาม
        try:
            field = Field.objects.get(id=data['field'])
            data['field'] = field.id
        except Field.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'ไม่พบสนามที่ระบุ (ID: {data["field"]})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # สร้าง serializer
        serializer = ReservationSerializer(data=data)
        
        if serializer.is_valid():
            # บันทึกการจอง
            reservation = serializer.save()
            
            return Response({
                'status': 'success',
                'reservation_id': reservation.id,
                'reservation': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            # แสดงข้อผิดพลาดการตรวจสอบ
            print("Validation errors:", serializer.errors)
            return Response({
                'status': 'error',
                'message': 'ข้อมูลไม่ถูกต้อง',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print("Exception in create_reservation:", str(e))
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)