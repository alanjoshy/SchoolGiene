from django.urls import path
from . import views
from chatapp.views import chat_view

urlpatterns = [
    path("", views.home, name="home"),
    # admin login
    path("admin_login/", views.admin_login, name="admin_login"),
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin_logout/", views.admin_logout, name="admin_logout"),
    path("add_course/", views.add_course, name="add_course"),
    path("add_subject/", views.add_subject, name="add_subject"),
    path("manage_course/", views.manage_course, name="manage_course"),
    path("add_subject/", views.add_subject, name="add_subject"),
    path("manage_subject/", views.manage_subject, name="manage_subject"),
    # admin student urls
    path("manage_student/", views.manage_student, name="manage_student"),
    path("student/approve/<int:student_id>/",views.approve_student,name="approve_student"), 
    path("register_student/", views.register_student, name="register_student"),
    path("add_session/", views.add_session, name="add_session"),
    path("manage_session/", views.manage_session, name="manage_session"),
    path("add_exam/", views.add_exam, name="add_exam"),
    path("manage_exam/", views.manage_exam, name="manage_exam"),
    path("view_attendance/", views.view_attendance, name="view_attendance"),
    path("student_view_leave/", views.student_view_leave, name="student_view_leave"),
    # admin staff urls
    path("manage_staff/", views.manage_staff, name="manage_staff"),
    path("register/staff/", views.staff_register, name="staff_register"),
    path("staff_view_leave/", views.staff_view_leave, name="staff_view_leave"),
    path('student_leave/update-status/<int:leave_id>/', views.student_update_leave_status, name='student_update_leave_status'),
    path('admin_student_feedback/', views.admin_student_feedback, name='admin_student_feedback'),
    path('admin_staff_feedback/', views.admin_staff_feedback, name='admin_staff_feedback'),
    # fee management
    path('add_fee/', views.add_fee, name='add_fee'),
    # chat
    path('chat/<str:username>/', chat_view, name='chat_view'), 
   
    
    
]
