from django.shortcuts import render, get_object_or_404
from .models import Message
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from adminapp.models import SchoolUser
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

User = get_user_model()

@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'user_list.html', {'users': users})

@login_required
def chat_view(request, username):
    users = User.objects.exclude(id=request.user.id)
    user_to_chat = get_object_or_404(User, username=username)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=user_to_chat) |
        Q(sender=user_to_chat, receiver=request.user)
    ).order_by('timestamp')

    return render(request, 'chat.html', {
        'user_to_chat': user_to_chat,
        'messages': messages,
        'users': users
    })

@login_required
def send_message(request, receiver_username):
    if request.method == 'POST':
        try:
            content = json.loads(request.body).get('content')
            receiver = SchoolUser.objects.get(username=receiver_username)
            sender = request.user

            if content:
                # Create and save the message
                message = Message.objects.create(sender=sender, receiver=receiver, content=content)
                return JsonResponse({
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%H:%M'),
                })
            else:
                return JsonResponse({'error': 'Message content is empty'}, status=400)

        except SchoolUser.DoesNotExist:
            return JsonResponse({'error': 'Receiver not found'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def fetch_messages(request, username):
    user_to_chat = get_object_or_404(User, username=username)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=user_to_chat) |
        Q(sender=user_to_chat, receiver=request.user)
    ).order_by('timestamp')

    messages_data = [
        {
            'sender': message.sender.username,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for message in messages
    ]
    return JsonResponse(messages_data, safe=False)
