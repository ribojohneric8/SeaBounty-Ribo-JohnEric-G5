from django.contrib import admin

from .models import SeafoodCategory, Stall


@admin.register(SeafoodCategory)
class SeafoodCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Stall)
class StallAdmin(admin.ModelAdmin):
    list_display = ("stall_name", "owner", "location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("stall_name", "location", "owner__email")
