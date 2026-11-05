from django.urls import path

from . import views

# Namespace, so templates use {% url 'exercises:exercise_list' %}.
app_name = "exercises"

urlpatterns = [
    path("", views.exercise_list, name="exercise_list"),
    path("new/", views.exercise_create, name="exercise_create"),
    path("<int:pk>/", views.exercise_detail, name="exercise_detail"),
    path("<int:pk>/edit/", views.exercise_update, name="exercise_update"),
    path("quick-add/", views.exercise_quick_add, name="exercise_quick_add"),
    path("<int:pk>/variant/", views.exercise_variant_create, name="exercise_variant_create"),
]
