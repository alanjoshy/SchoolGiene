from django.urls import path
from . import views

urlpatterns = [
    # home page initial page 
    path('', views.home, name='home'),
    # admin login
    path('admin_login/', views.admin_login, name='admin_login'), 
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),   
    path('admin_logout/',views.admin_logout,name='admin_logout'),
    path('add_course/',views.add_course,name='add_course'),
    path('add_subject/',views.add_subject,name='add_subject'), 
    path('manage_course/', views.manage_course, name='manage_course'),
    path('add_subject/', views.add_subject, name='add_subject'),
    path('manage_subject/', views.manage_subject, name='manage_subject'),
    # admin student urls
    path('manage_student/', views.manage_student, name='manage_student'),
    path('student/approve/<int:student_id>/', views.approve_student, name='approve_student'),
    path('register_student/', views.register_student, name='register_student'),
    # admin staff urls
    path('manage_staff/', views.manage_staff, name='manage_staff'),
    
]


