from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('reservation/', views.reservation_view, name='reservation'),
    path('api/fields/', views.get_fields, name='get_fields'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/create-reservation/', views.create_reservation, name='create_reservation'),
]