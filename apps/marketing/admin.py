from django.contrib import admin

from .models import BlogPost, ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "interest_type", "company_name", "is_contacted", "created_at")
    list_filter = ("interest_type", "is_contacted")
    search_fields = ("name", "email", "company_name", "message")
    date_hierarchy = "created_at"
    actions = ["mark_contacted"]

    @admin.action(description="Mark selected submissions as contacted")
    def mark_contacted(self, request, queryset):
        queryset.update(is_contacted=True)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "is_published", "published_at")
    list_filter = ("is_published",)
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
