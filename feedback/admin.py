from django.contrib import admin

from .models import Feedback, Status


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "kind", "status", "short_message", "user", "device", "page")
    list_display_links = ("id", "short_message")
    list_editable = ("status",)  # change the status straight from the list
    list_filter = ("status", "kind", "device")
    search_fields = ("message", "page", "user__email", "user__username")
    date_hierarchy = "created_at"
    readonly_fields = ("user", "kind", "message", "page", "device", "user_agent", "created_at")
    fields = ("status", "kind", "message", "page", "user", "device", "user_agent", "created_at")
    actions = ("mark_in_progress", "mark_done")

    @admin.display(description="treść")
    def short_message(self, obj):
        return obj.message if len(obj.message) <= 80 else obj.message[:80] + "…"

    @admin.action(description="Oznacz jako: w trakcie")
    def mark_in_progress(self, request, queryset):
        queryset.update(status=Status.IN_PROGRESS)

    @admin.action(description="Oznacz jako: załatwione")
    def mark_done(self, request, queryset):
        queryset.update(status=Status.DONE)

    def has_add_permission(self, request):
        return False  # reports come from the app, not from the admin
