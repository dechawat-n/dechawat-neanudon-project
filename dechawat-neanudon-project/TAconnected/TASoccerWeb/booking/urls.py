from django.urls import path
from . import Booking_api
from LoginSystem.views import LoginViews
from .views_admin import fields_management_view

urlpatterns = [
    path('reservation/', Booking_api.reservation_view, name='reservation'),
    path('api/fields/', Booking_api.get_fields, name='get_fields'),
    path('api/create-reservation/', Booking_api.create_reservation, name='create_reservation'),
    path('api/check-availability/', Booking_api.check_availability, name='check_availability'),  # เพิ่มบรรทัดนี้
    path('pre_reserve/', Booking_api.pre_reservation_view, name='pre-reserve'),
    
    path('big-reservation/',Booking_api.BigReserveView,name='bigreserve'),
    path('medium-reservation/',Booking_api.MediumReserveView,name='mediumreserve'),
    path('small-reservation/',Booking_api.SmallReserveView,name='smallreserve'),
    path('admin/fields-management/', fields_management_view, name='fields_management'),

]