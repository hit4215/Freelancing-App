from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'reviewer', 'reviewee', 'star_display', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer__username', 'reviewee__username', 'comment', 'contract__job__title')

    def star_display(self, obj):
        return f"{obj.rating} ★"
    star_display.short_description = "Rating"
