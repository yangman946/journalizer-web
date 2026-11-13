from django.urls import path
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("accounts/login/", views.login, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path('', views.home, name='home'),
    path('write/', views.write, name='main-write'),
    path('archieve/', views.archieve, name='archieve'),
    path('archieve/<xyear>/<xmonth>/<id>/', views.read, name='read')
]