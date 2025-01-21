from django.urls import include, path

from app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('map/', views.map, name='map'),
    path('organ/<int:organ_id>/', views.organ_page, name='organ'),
    path('r/', views.redirect, name='redirect'),  # keep track of hits to OHTA URLs
    path('login/', views.send_login_code, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-login-code/', views.verify_login_code, name='verify_login_code'),
    path('app/', views.app_view, name='app'),
    path('api/bookmark/', views.bookmark_organ, name='bookmark'),
    path('api/check_bookmark/', views.check_bookmark, name='check_bookmark'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
]