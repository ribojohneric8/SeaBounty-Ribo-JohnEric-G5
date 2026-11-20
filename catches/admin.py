from django.contrib import admin

from .models import CatchUpdate


@admin.register(CatchUpdate)
class CatchUpdateAdmin(admin.ModelAdmin):
    list_display = ("category", "stall", "price_per_kg", "posted_by", "date_posted")
    list_filter = ("category",)
    search_fields = ("stall__stall_name", "category__name")
