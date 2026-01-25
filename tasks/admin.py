from django.contrib import admin
from .models import Day, Task


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date",
        "status",
        "is_active",
        "created_at",
        "closed_at",
    )

    list_filter = ("status", "is_active", "date")
    search_fields = ("user__username",)
    ordering = ("-date",)
    date_hierarchy = "date"

    readonly_fields = ("created_at", "closed_at")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "day",
        "status",
        "created_at",
    )

    list_filter = ("status", "day__date")
    search_fields = ("title", "user__username")
    ordering = ("-created_at",)

    readonly_fields = ("created_at",)
