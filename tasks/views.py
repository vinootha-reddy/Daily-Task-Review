from datetime import date
from django.contrib.auth.decorators import login_required   
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import TaskStatus, Day
from .services import get_active_day, get_open_days, set_active_day, \
    create_task, toggle_task_status, delete_task, \
    close_active_day_and_open_next
from django.shortcuts import render, redirect, get_object_or_404


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('today')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            from .services import ensure_first_day
            ensure_first_day(user) 

            return redirect('today')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


@require_POST
def add_task(request):
    title = request.POST.get('title', '').strip()
    if title:
        create_task(request.user, title)
    return redirect('today')


@require_POST
def toggle_task(request, task_id):
    toggle_task_status(task_id)
    return redirect('today')


@require_POST
def close_day(request):
    user = user = request.user
    task_ids = request.POST.getlist('carry_tasks')
    close_active_day_and_open_next(user, task_ids)
    return redirect('today')


@login_required
def today_view(request):
    user = request.user

    day = get_active_day(user)

    all_days = Day.objects.filter(user=user).order_by("-date")
    open_days = get_open_days(user).exclude(id=day.id)

    return render(request, "tasks/today.html", {
        "day": day,
        "all_days": all_days,
        "open_days": open_days,
        "incomplete_tasks": day.tasks.filter(status=TaskStatus.PENDING),
        "completed_tasks": day.tasks.filter(status=TaskStatus.COMPLETED),
    })


def day_view(request, day_id):
    """
    View any day (calendar navigation)
    """
    user = request.user
    day = get_object_or_404(Day, id=day_id, user=user)
    active_day = get_active_day(user)

    return render(request, "tasks/day.html", {
        "day": day,
        "is_active": day.is_active,
        "is_open": day.status == "OPEN",
        "incomplete_tasks": day.tasks.filter(status=TaskStatus.PENDING),
        "completed_tasks": day.tasks.filter(status=TaskStatus.COMPLETED),
        "all_days": Day.objects.filter(user=user).order_by("-date"),
        "active_day": active_day,
    })


@require_POST
def add_task_view(request):
    title = request.POST.get("title", "").strip()
    if title:
        create_task(request.user, title)
    return redirect("today")


@require_POST
def toggle_task_view(request, task_id):
    toggle_task_status(task_id)
    return redirect("today")


@require_POST
def delete_task_view(request, task_id):
    delete_task(task_id)
    return redirect("today")


@require_POST
def set_active_day_view(request, day_id):
    user = request.user
    day = get_object_or_404(Day, id=day_id, user=user)
    set_active_day(user, day)
    return redirect("today")


@require_POST
def close_active_day_view(request):
    user = request.user
    carry_task_ids = request.POST.getlist("carry_tasks")
    close_active_day_and_open_next(user, carry_task_ids)
    return redirect("today")


@login_required
def account_view(request):
    user = request.user
    return render(request, "tasks/account.html", {
        "user": user,
    })
