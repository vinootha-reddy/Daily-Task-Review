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
        return day

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


def get_active_day(user):
    active = Day.objects.filter(user=user, is_active=True).first()
    if active:
        return active

    today = timezone.localdate()
    day, _ = Day.objects.get_or_create(user=user, date=today)
    day.is_active = True
    day.save(update_fields=["is_active"])
    return day


def get_open_days(user):
    return Day.objects.filter(user=user, status=DayStatus.OPEN).order_by("date")


def set_active_day(user, day):
    Day.objects.filter(user=user, is_active=True).update(is_active=False)
    day.is_active = True
    day.save(update_fields=["is_active"])


def create_task(user, title):
    day = get_active_day(user)
    return Task.objects.create(user=user, day=day, title=title)


def delete_task(task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.day.status == DayStatus.CLOSED:
        return

    task.delete()


@transaction.atomic
def close_day(day):
    if day.status == DayStatus.CLOSED:
        return

    day.status = DayStatus.CLOSED
    day.closed_at = timezone.now()
    day.is_active = False
    day.save(update_fields=["status", "closed_at", "is_active"])


@transaction.atomic
def close_active_day_and_open_next(user, carry_task_ids):
    today = get_active_day(user)

    tomorrow_date = today.date + timezone.timedelta(days=1)
    tomorrow, _ = Day.objects.get_or_create(user=user, date=tomorrow_date)

    for task in today.tasks.filter(id__in=carry_task_ids, status=TaskStatus.PENDING):
        Task.objects.create(
            user=user,
            day=tomorrow,
            title=task.title,
        )

    close_day(today)

    set_active_day(user, tomorrow)

    return tomorrow
