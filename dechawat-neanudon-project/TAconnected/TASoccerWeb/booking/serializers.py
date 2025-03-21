from rest_framework import serializers
from .models import Field, Reservation
from datetime import datetime, time

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ['id', 'name', 'capacity', 'price_per_hour']

class ReservationSerializer(serializers.ModelSerializer):
    field_name = serializers.ReadOnlyField(source='field.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    
    start_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H.%M'])
    end_time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M', '%H.%M'])
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'field', 'field_name', 'reservation_date', 
            'start_time', 'end_time', 'customer_name', 
            'phone', 'status', 'status_display', 'total_price', 'created_at'
        ]
        read_only_fields = ['created_at']
        
    def validate(self, data):
        """
        ตรวจสอบความซ้อนทับของเวลาจอง
        """
        # ดึงข้อมูลที่จำเป็น
        field = data.get('field')
        reservation_date = data.get('reservation_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # กรณีพิเศษสำหรับเวลาสิ้นสุด 00:00
        if end_time == time(0, 0):
            end_time = time(23, 59, 59)

        # ตรวจสอบการจองที่มีอยู่แล้ว
        overlapping_reservations = Reservation.objects.filter(
            field=field,
            reservation_date=reservation_date,
            status__in=['pending', 'booked']
        )

        # ตรวจสอบการซ้อนทับของเวลา
        for res in overlapping_reservations:
            res_start = res.start_time
            res_end = res.end_time if res.end_time != time(0, 0) else time(23, 59, 59)

            # เงื่อนไขการซ้อนทับ
            if (
                (start_time >= res_start and start_time < res_end) or
                (end_time > res_start and end_time <= res_end) or
                (start_time <= res_start and end_time >= res_end)
            ):
                raise serializers.ValidationError({
                    'time_error': f'ช่วงเวลา {start_time}-{end_time} ซ้อนทับกับการจองอื่น'
                })

        return data

class ReservationConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['status']
        read_only_fields = ['field', 'reservation_date', 'start_time', 'end_time', 
                          'customer_name', 'phone', 'total_price', 'created_at']