from django.contrib import admin
from .models import Category, Job, Proposal, Contract

class ProposalInline(admin.TabularInline):
    model = Proposal
    extra = 0
    readonly_fields = ('freelancer', 'bid_amount', 'estimated_days', 'created_at')
    fields = ('freelancer', 'bid_amount', 'estimated_days', 'status', 'created_at')
    can_delete = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'job_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

    def job_count(self, obj):
        return obj.jobs.count()
    job_count.short_description = "Active Jobs"

@admin.action(description="Mark selected jobs as CLOSED")
def close_jobs(modeladmin, request, queryset):
    queryset.update(status='CLOSED')

@admin.action(description="Mark selected jobs as OPEN")
def open_jobs(modeladmin, request, queryset):
    queryset.update(status='OPEN')

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'category', 'budget_type', 'budget_min', 'budget_max', 'status', 'proposal_count', 'created_at')
    list_filter = ('status', 'budget_type', 'experience_level', 'category', 'created_at')
    search_fields = ('title', 'description', 'client__username', 'client__email')
    filter_horizontal = ('skills',)
    actions = [close_jobs, open_jobs]
    inlines = [ProposalInline]
    date_hierarchy = 'created_at'

@admin.action(description="Accept selected proposals")
def accept_proposals(modeladmin, request, queryset):
    queryset.update(status='ACCEPTED')

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('job', 'freelancer', 'bid_amount', 'estimated_days', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('job__title', 'freelancer__username', 'cover_letter')
    actions = [accept_proposals]
    date_hierarchy = 'created_at'

@admin.action(description="Mark selected contracts as COMPLETED")
def complete_contracts(modeladmin, request, queryset):
    from django.utils import timezone
    queryset.update(status='COMPLETED', completed_at=timezone.now())

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'client', 'freelancer', 'total_amount', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('job__title', 'client__username', 'freelancer__username')
    actions = [complete_contracts]
    date_hierarchy = 'created_at'
