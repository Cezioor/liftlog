from django.urls import path

from . import views

app_name = "workouts"

urlpatterns = [
    path("start/", views.workout_start, name="workout_start"),
    path("<int:pk>/", views.workout_detail, name="workout_detail"),
    path("<int:pk>/finish/", views.workout_finish, name="workout_finish"),
    path("<int:pk>/discard/", views.workout_discard, name="workout_discard"),
    path("<int:pk>/exercises/<int:exercise_pk>/", views.exercise_card, name="exercise_card"),
    path("<int:pk>/exercises/<int:exercise_pk>/sets/", views.set_create, name="set_create"),
    path("sets/<int:pk>/edit/", views.set_update, name="set_update"),
    path("sets/<int:pk>/delete/", views.set_delete, name="set_delete"),
]
