from django.contrib import admin
from django.urls import path
from analyzer import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("analyze/", views.analyze, name="analyze"),
    path("history/", views.history, name="history"),
    path("history/<int:pk>/", views.history_detail, name="history_detail"),
    path("history/<int:pk>/delete/", views.history_delete, name="history_delete"),
]
