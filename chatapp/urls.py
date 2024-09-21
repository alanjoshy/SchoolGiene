from django.urls import path
from . import views

urlpatterns = [
    path('chat/<str:username>/', views.chat_view, name='chat'),
    path('send-message/<str:receiver_username>/', views.send_message, name='send_message'),
    path('fetch-messages/<str:username>/', views.fetch_messages, name='fetch_messages'),
]
