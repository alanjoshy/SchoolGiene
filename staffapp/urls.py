from django.urls import path
from . import views 
from chatapp.views import chat_view

urlpatterns = [
    path('staff_register', views.staff_register, name='staff_register'),
    path('staff_login', views.staff_login, name='staff_login'),
    path('staff_dashboard',views.staff_dashboard,name='staff_dashboard'),
    path('staff_logout', views.staff_logout, name='staff_logout'),
    path('take_attendance', views.take_attendance, name='take_attendance'),
    path('view_student_attendance', views.view_student_attendance, name='view_student_attendance'),
    path('view_results', views.view_results, name='view_results'),
    path('add_result', views.add_result, name='add_result'),
    path('staff_apply_leave/', views.staff_apply_leave, name='staff_apply_leave'), 
    path('staff_feedback/', views.staff_feedback, name='staff_feedback'),
    path('chat/<str:username>/', chat_view, name='chat_view'), 
    path('staff_forgot-password/', views.staff_forgot_password_request, name='staff_forgot_password_request'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('enter-reset-code/', views.enter_reset_code, name='enter_reset_code'),  # Page to enter reset code
    
     
]