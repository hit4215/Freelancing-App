from django.urls import path
from . import views

urlpatterns = [
    path('contract/<int:contract_id>/', views.create_review_view, name='create_review'),
]
