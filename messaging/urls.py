from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('<int:conversation_id>/', views.inbox_view, name='conversation_detail'),
    path('start/<int:user_id>/', views.start_conversation_view, name='start_conversation'),
    path('<int:conversation_id>/send/', views.send_message_view, name='send_message'),
    path('<int:conversation_id>/fetch/', views.fetch_messages_api, name='fetch_messages_api'),
]
