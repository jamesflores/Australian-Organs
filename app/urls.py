from django.urls import include, path

from app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('map/', views.map, name='map'),
    path('organ/<int:organ_id>/', views.organ_page, name='organ'),
    path('r/', views.redirect, name='redirect'),  # keep track of hits to OHTA URLs
    path('request-magic-link/', views.request_magic_link, name='request_magic_link'),
    path('login/', views.login_with_magic_link, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('app/', views.app_view, name='app'),
    path('api/bookmark/', views.bookmark_organ, name='bookmark'),
    path('api/check_bookmark/', views.check_bookmark, name='check_bookmark'),
]