from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('freelancers/', views.freelancer_directory_view, name='freelancers'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('platform-admin/', views.platform_admin_view, name='platform_admin'),
    path('admin-panel/', views.admin_gateway_view, name='admin_gateway'),
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
]
