from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup),
    path('login', views.login),
    path('taxi', views.new_taxi),
    path('coordinate', views.coordinate),
    path('me', views.user_info),
    path('addresses', views.addresses),
    path('sendmail', views.urgent_call),
    path('new/addresses', views.new_address),
    path('new/protectors', views.new_protector),
    path('taxies', views.taxies),
    # path('nearby-taxi', views.nearby_taxi),
    path('call-taxi', views.call_taxi)

]