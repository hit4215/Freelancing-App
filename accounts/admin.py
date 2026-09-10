from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Skill, PortfolioItem

class PortfolioItemInline(admin.TabularInline):
    model = PortfolioItem
    extra = 0
    fields = ('title', 'project_url', 'tags', 'created_at')
    readonly_fields = ('created_at',)

@admin.action(description="Boost Job Success Score to 100% & Set Available")
def verify_and_boost_freelancer(modeladmin, request, queryset):
    queryset.update(job_success_score=100, is_available_for_hire=True)

@admin.action(description="Set Available for Hire = False")
def set_unavailable(modeladmin, request, queryset):
    queryset.update(is_available_for_hire=False)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Freelance & Client Profile', {
            'fields': ('role', 'headline', 'bio', 'hourly_rate', 'location',
                       'phone', 'company_name', 'website', 'github', 'skills',
                       'experience_level', 'avatar_url', 'is_available_for_hire',
                       'job_success_score', 'total_earned', 'total_spent')
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'hourly_rate', 'job_success_score', 'is_available_for_hire', 'is_staff')
    list_filter = ('role', 'experience_level', 'is_available_for_hire', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'headline', 'company_name')
    filter_horizontal = ('skills', 'groups', 'user_permissions')
    actions = [verify_and_boost_freelancer, set_unavailable]
    inlines = [PortfolioItemInline]

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'users_count')
    list_filter = ('category',)
    search_fields = ('name', 'category')

    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = "Specialists"

@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'project_url', 'tags', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'user__username', 'tags', 'description')
