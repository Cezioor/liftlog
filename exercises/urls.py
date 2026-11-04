from django.urls import path

from . import views

# Namespace, so templates use {% url 'exercises:exercise_list' %}.
app_name = "exercises"

urlpatterns = [
    path("", views.exercise_list, name="exercise_list"),
    path("new/", views.exercise_create, name="exercise_create"),
    path("<int:pk>/edit/", views.exercise_update, name="exercise_update"),
]
