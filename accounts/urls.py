from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/portfolio/add/', views.add_portfolio_view, name='add_portfolio'),
    path('profile/portfolio/<int:pk>/delete/', views.delete_portfolio_view, name='delete_portfolio'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('save/<int:freelancer_id>/', views.toggle_save_freelancer_view, name='toggle_save_freelancer'),
]
