from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import Booking_api
from .api_views import FieldViewSet, ReservationViewSet, check_availability, create_reservation
from LoginSystem.views import LoginViews

# สร้าง Router สำหรับ REST API
router = DefaultRouter()
router.register(r'fields', FieldViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    # API Endpoints
    path('api/', include(router.urls)),
    path('api/check-availability/', check_availability, name='api_check_availability'),
    path('api/create-reservation/', create_reservation, name='api_create_reservation'),
    
    # หน้าเว็บต่างๆ
    path('pre_reserve/', Booking_api.pre_reservation_view, name='pre-reserve'),
    path('reservation/', Booking_api.reservation_view, name='reservation'),
    path('big-reservation/', Booking_api.BigReserveView, name='bigreserve'),
    path('medium-reservation/', Booking_api.MediumReserveView, name='mediumreserve'),
    path('small-reservation/', Booking_api.SmallReserveView, name='smallreserve'),
]