from django.urls import path
from . import views
from tasks.views import signup_view

urlpatterns = [
    # pages
    path("", views.today_view, name="today"),
    path("day/<int:day_id>/", views.day_view, name="day_view"),

    # actions
    path("__init_admin__/", views.create_superuser_once),
    path("add/", views.add_task_view, name="add_task"),
    path("toggle/<int:task_id>/", views.toggle_task_view, name="toggle_task"),
    path("delete/<int:task_id>/", views.delete_task_view, name="delete_task"),
    path("set-active/<int:day_id>/", views.set_active_day_view, name="set_active_day"),
    path("close-active/", views.close_active_day_view, name="close_active_day"),
    path('accounts/signup/', signup_view, name='signup'),
]
