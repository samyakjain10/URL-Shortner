from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('<slug:short_code>/', views.linkDashboard),
    path('delete/<slug:short_code>/', views.linkDelete)
]
