from django.urls import path
from . import views 

urlpatterns = [
    path('register_student/', views.register_student, name='register_student'),
    path('student_login/', views.student_login, name='student_login'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student_logout/', views.student_logout, name='student_logout'),   
    path('result_view/', views.result_view, name='result_view'),  
    path('attendance_view/', views.attendance_view, name='attendance_view'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('student_apply_leave/', views.student_apply_leave, name='student_apply_leave'),   
    path('student_feedback/', views.student_feedback, name='student_feedback'),
    path('student_profile_update/', views.student_profile_update, name='student_profile_update'),
  
]