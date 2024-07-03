from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup),
    path('login', views.login),
    path('taxi', views.new_taxi),
    path('coordinate', views.coordinate),
    path('me', views.user_info),
]