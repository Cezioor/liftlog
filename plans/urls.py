from django.urls import path

from . import views

app_name = "plans"

urlpatterns = [
    path("", views.plan_list, name="plan_list"),
    path("new/", views.plan_create, name="plan_create"),
    path("<int:pk>/", views.plan_detail, name="plan_detail"),
    path("<int:pk>/activate/", views.plan_activate, name="plan_activate"),
    path("<int:pk>/delete/", views.plan_delete, name="plan_delete"),
    path("<int:plan_pk>/days/new/", views.day_create, name="day_create"),
    path("days/<int:pk>/edit/", views.day_update, name="day_update"),
    path("days/<int:pk>/delete/", views.day_delete, name="day_delete"),
    path("days/<int:pk>/move/<str:direction>/", views.day_move, name="day_move"),
    path("days/<int:day_pk>/exercises/new/", views.plan_exercise_create, name="pe_create"),
    path("exercises/<int:pk>/edit/", views.plan_exercise_update, name="pe_update"),
    path("exercises/<int:pk>/delete/", views.plan_exercise_delete, name="pe_delete"),
    path("exercises/<int:pk>/move/<str:direction>/", views.plan_exercise_move, name="pe_move"),
]
