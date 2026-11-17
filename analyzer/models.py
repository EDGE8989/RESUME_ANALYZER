from django.db import models


class Analysis(models.Model):
    original_text = models.TextField()
    corrected_text = models.TextField()
    issues = models.JSONField(default=list)
    word_count = models.PositiveIntegerField(default=0)
    issue_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis {self.pk} — {self.created_at:%Y-%m-%d %H:%M}"
