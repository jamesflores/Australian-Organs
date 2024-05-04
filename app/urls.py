from django.urls import include, path

from app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('map/', views.map, name='map'),
    path('r/', views.redirect, name='redirect'),  # keep track of hits to OHTA URLs
]