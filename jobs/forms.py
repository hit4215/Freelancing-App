from django import forms
from .models import Job, Proposal, Category, ContractMilestone, JobInvitation
from accounts.models import Skill

class JobForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=Job.STATUS_CHOICES,
        required=False,
        initial='OPEN',
        widget=forms.Select(attrs={'class': 'form-control select-modern'})
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2-modern', 'size': 5})
    )

    def clean_status(self):
        status = self.cleaned_data.get('status')
        return status or 'OPEN'

    class Meta:
        model = Job
        fields = (
            'title', 'category', 'status', 'description', 'budget_type',
            'budget_min', 'budget_max', 'experience_level',
            'location_type', 'deadline_days', 'skills'
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Build an AI-Powered Healthcare Dashboard in Django & Next.js'}),
            'category': forms.Select(attrs={'class': 'form-control select-modern'}),
            'status': forms.Select(attrs={'class': 'form-control select-modern'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Detail the scope, deliverables, technologies, and milestones...'}),
            'budget_type': forms.Select(attrs={'class': 'form-control select-modern'}),
            'budget_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min Budget ($)'}),
            'budget_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Budget ($)'}),
            'experience_level': forms.Select(attrs={'class': 'form-control select-modern'}),
            'location_type': forms.Select(attrs={'class': 'form-control select-modern'}),
            'deadline_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '14'}),
        }


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ('bid_amount', 'estimated_days', 'cover_letter')
        widgets = {
            'bid_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 750', 'step': '1.00'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10'}),
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Explain why you are the best fit, your past relevant experience, and how you will execute this project...'}),
        }


class ContractMilestoneForm(forms.ModelForm):
    class Meta:
        model = ContractMilestone
        fields = ('title', 'description', 'amount', 'due_date', 'order')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Phase 1: Database Architecture & Core API'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Scope of deliverables for this milestone...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '250.00', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1'}),
        }


class MilestoneSubmissionForm(forms.ModelForm):
    class Meta:
        model = ContractMilestone
        fields = ('submission_notes', 'submission_url')
        widgets = {
            'submission_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe work completed, test verification notes, and deliverables...'}),
            'submission_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/... or preview URL'}),
        }


class JobInvitationForm(forms.ModelForm):
    def __init__(self, *args, client=None, **kwargs):
        super().__init__(*args, **kwargs)
        if client:
            self.fields['job'].queryset = Job.objects.filter(client=client, status='OPEN')

    class Meta:
        model = JobInvitation
        fields = ('job', 'message')
        widgets = {
            'job': forms.Select(attrs={'class': 'form-control select-modern'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'We reviewed your profile and would love for you to submit a proposal on our job...'}),
        }

