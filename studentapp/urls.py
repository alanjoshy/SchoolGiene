from django.urls import path
from . import views 

urlpatterns = [
    path('student_register/', views.student_register, name='student_register'),
    path('student_login/', views.student_login, name='student_login'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student_logout/', views.student_logout, name='student_logout'),   
]