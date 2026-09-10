from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('post/', views.create_job_view, name='create_job'),
    path('<slug:slug>/', views.job_detail_view, name='job_detail'),
    path('<slug:slug>/edit/', views.edit_job_view, name='edit_job'),
    path('<slug:slug>/status/', views.update_job_status_view, name='update_job_status'),
    path('<slug:slug>/save/', views.toggle_save_job_view, name='toggle_save_job'),
    path('<slug:slug>/apply/', views.submit_proposal_view, name='submit_proposal'),
    path('proposal/<int:proposal_id>/accept/', views.accept_proposal_view, name='accept_proposal'),
    path('contract/<int:contract_id>/', views.contract_detail_view, name='contract_detail'),
    path('contract/<int:contract_id>/complete/', views.complete_contract_view, name='complete_contract'),
    path('contract/<int:contract_id>/milestones/add/', views.add_milestone_view, name='add_milestone'),
    path('milestones/<int:milestone_id>/submit/', views.submit_milestone_view, name='submit_milestone'),
    path('milestones/<int:milestone_id>/approve/', views.approve_milestone_view, name='approve_milestone'),
    path('milestones/<int:milestone_id>/revision/', views.request_revision_view, name='request_revision'),
    path('invoice/<int:invoice_id>/', views.invoice_detail_view, name='invoice_detail'),
    path('invite/<int:freelancer_id>/', views.invite_freelancer_view, name='invite_freelancer'),
    path('invitation/<int:invitation_id>/<str:action>/', views.respond_invitation_view, name='respond_invitation'),
]
