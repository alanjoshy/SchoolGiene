from django.urls import path
from . import views 
from chatapp.views import chat_view
from paymentapp.views import create_payment

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
    path('chat/<str:username>/', chat_view, name='chat_view'), 
    path('create_payment/<int:fee_id>/', create_payment, name='create_payment'),
    path('fee_section/', views.fee_section, name='fee_section'), 
    path('forgot-password/', views.forgot_password_request, name='forgot_password_request'),
    path('reset-password/<str:username>/', views.reset_password, name='reset_password'),
  
]   