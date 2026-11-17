from django.contrib import admin
from .models import Analysis

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "word_count", "issue_count")
    ordering = ("-created_at",)
