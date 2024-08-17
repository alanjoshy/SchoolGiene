from django.urls import path
from . import views 

urlpatterns = [
     path('staff_register', views.staff_register, name='staff_register'),
    path('staff_login', views.staff_login, name='staff_login'),
    path('staff_dashboard',views.staff_dashboard,name='staff_dashboard'),
    path('staff_logout', views.staff_logout, name='staff_logout'),
    path('take_attendance', views.take_attendance, name='take_attendance'),
    path('view_attendance', views.view_attendance, name='view_attendance'),
]