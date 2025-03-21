from rest_framework import serializers
from .models import Field, Reservation

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ['id', 'name', 'capacity', 'price_per_hour']

class ReservationSerializer(serializers.ModelSerializer):
    field_name = serializers.ReadOnlyField(source='field.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    
    # อาจจำเป็นต้องแปลงค่าเริ่มต้นให้ถูกต้อง
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
        ตรวจสอบว่าเวลาเริ่มต้นต้องมาก่อนเวลาสิ้นสุด ยกเว้นกรณีพิเศษสำหรับเที่ยงคืน
        """
        start_time = data['start_time']
        end_time = data['end_time']
        
        # กรณีพิเศษสำหรับเที่ยงคืน (00:00)
        if end_time.hour == 0 and end_time.minute == 0:
            return data  # ยอมรับการจองที่สิ้นสุดเที่ยงคืน
            
        if start_time >= end_time:
            raise serializers.ValidationError(
                {"time_error": "เวลาเริ่มต้นต้องมาก่อนเวลาสิ้นสุด"}
            )
        return data

class ReservationConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['status']
        read_only_fields = ['field', 'reservation_date', 'start_time', 'end_time', 
                          'customer_name', 'phone', 'total_price', 'created_at']