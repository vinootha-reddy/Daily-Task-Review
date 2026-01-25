from datetime import date
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Day, Task, TaskStatus, DayStatus


def ensure_first_day(user):
    if not Day.objects.filter(user=user).exists():
        Day.objects.create(
            user=user,
            date=date.today(),
            status="OPEN",
            is_active=True
        )
        

def get_active_day(user):
    today = timezone.localdate()
    day, _ = Day.objects.get_or_create(user=user, date=today)

    if day.status == DayStatus.CLOSED:
        tomorrow = today + timezone.timedelta(days=1)
        day, _ = Day.objects.get_or_create(user=user, date=tomorrow)

    return day


def create_task(user, title):
    day = get_active_day(user)
    return Task.objects.create(user=user, day=day, title=title)


def toggle_task_status(task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.day.status == DayStatus.CLOSED:
        return task

    task.status = (
        TaskStatus.COMPLETED
        if task.status == TaskStatus.PENDING
        else TaskStatus.PENDING
    )

    task.save(update_fields=['status'])
    return task


@transaction.atomic
def close_day_and_carry_forward(user, carry_task_ids):
    day = get_active_day(user)

    if day.status == DayStatus.CLOSED:
        return day  # no exception, safe idempotent behavior

    tomorrow = Day.objects.create(
        user=user,
        date=day.date + timezone.timedelta(days=1)
    )

    for task in day.tasks.filter(id__in=carry_task_ids, status=TaskStatus.PENDING):
        Task.objects.create(
            user=user,
            day=tomorrow,
            title=task.title,
            priority=task.priority,
            is_carried_forward=True,
            source_task=task
        )

    day.status = DayStatus.CLOSED
    day.closed_at = timezone.now()
    day.save(update_fields=['status', 'closed_at'])

    return tomorrow
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Day, Task, DayStatus, TaskStatus


# =========================
# Day helpers
# =========================

def get_active_day(user):
    """
    Returns the active day for the user.
    Creates today if none exists.
    Ensures only one active day exists.
    """

    active = Day.objects.filter(user=user, is_active=True).first()
    if active:
        return active

    today = timezone.localdate()
    day, _ = Day.objects.get_or_create(user=user, date=today)
    day.is_active = True
    day.save(update_fields=["is_active"])
    return day


def get_open_days(user):
    """
    Returns all open days (grace mode).
    """
    return Day.objects.filter(user=user, status=DayStatus.OPEN).order_by("date")


def set_active_day(user, day):
    """
    Switch active day (used when navigating calendar).
    """
    Day.objects.filter(user=user, is_active=True).update(is_active=False)
    day.is_active = True
    day.save(update_fields=["is_active"])


# =========================
# Task helpers
# =========================

def create_task(user, title):
    """
    Always adds task to ACTIVE day.
    """
    day = get_active_day(user)
    return Task.objects.create(user=user, day=day, title=title)


def toggle_task_status(task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.day.status == DayStatus.CLOSED:
        return task  # immutable

    task.status = (
        TaskStatus.COMPLETED
        if task.status == TaskStatus.PENDING
        else TaskStatus.PENDING
    )
    task.save(update_fields=["status"])
    return task


def delete_task(task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.day.status == DayStatus.CLOSED:
        return

    task.delete()


# =========================
# Closing logic
# =========================

@transaction.atomic
def close_day(day):
    """
    Close a day explicitly.
    """
    if day.status == DayStatus.CLOSED:
        return

    day.status = DayStatus.CLOSED
    day.closed_at = timezone.now()
    day.is_active = False
    day.save(update_fields=["status", "closed_at", "is_active"])


@transaction.atomic
def close_active_day_and_open_next(user, carry_task_ids):
    """
    Closes active day and creates tomorrow as active day.
    """
    today = get_active_day(user)

    # Create tomorrow
    tomorrow_date = today.date + timezone.timedelta(days=1)
    tomorrow, _ = Day.objects.get_or_create(user=user, date=tomorrow_date)

    # Carry forward selected tasks
    for task in today.tasks.filter(id__in=carry_task_ids, status=TaskStatus.PENDING):
        Task.objects.create(
            user=user,
            day=tomorrow,
            title=task.title,
        )

    # Close today
    close_day(today)

    # Activate tomorrow
    set_active_day(user, tomorrow)

    return tomorrow
