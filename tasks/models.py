from django.db import models
from django.contrib.auth.models import User


class DayStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class TaskStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    COMPLETED = "COMPLETED", "Completed"


class Day(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="days")
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=DayStatus.choices,
        default=DayStatus.OPEN,
    )
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} — {self.date} ({self.status})"


class Task(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tasks")
    day = models.ForeignKey(
        Day, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
