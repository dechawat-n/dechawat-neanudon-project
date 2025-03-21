from django.urls import path
from .views import LoginViews

urlpatterns = [
    path('dashboard/', LoginViews.admin_dashboard, name='admin_dashboard'),
    path('user/', LoginViews.admin_userManagement, name='admin_userManagement'),
    path('reservation/', LoginViews.admin_reservaionManagement, name='admin_reservationManagement'),
    path("admin-gallery/", LoginViews.admin_gallery, name="admin-gallery"),
]