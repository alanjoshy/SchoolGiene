from django.shortcuts import render, get_object_or_404
from .models import Message
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Q
from adminapp.models import SchoolUser
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.core.cache import cache
from django.utils.dateparse import parse_datetime
from datetime import datetime, time
import time

User = get_user_model()





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
@csrf_exempt
def send_message(request, receiver_username):
    try:
        data = json.loads(request.body)
        content = data.get('content')
        receiver = SchoolUser.objects.get(username=receiver_username)
        sender = request.user
        
        if content:
            # Create and save the message
            message = Message.objects.create(sender=sender, receiver=receiver, content=content)
            return JsonResponse({
                'status': 'success',
                'message': {
                    'content': message.content,
                    'sender': sender.username,
                    'timestamp': message.timestamp.isoformat(),
                }
            })
        else:
            return JsonResponse({'error': 'Message content is empty'}, status=400)
    
    except SchoolUser.DoesNotExist:
        return JsonResponse({'error': 'Receiver not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@login_required
def fetch_messages(request, username):
    user_to_chat = get_object_or_404(User, username=username)
    after_timestamp = request.GET.get('after')

    # Server-side debouncing
    cache_key = f'last_fetch_{request.user.id}_{user_to_chat.id}'
    last_fetch_time = cache.get(cache_key)
    current_time = time.time()

    if last_fetch_time and current_time - last_fetch_time < 1:  # 1 second debounce
        return JsonResponse([], safe=False)

    cache.set(cache_key, current_time, 60)  # Cache for 60 seconds

    messages_query = Message.objects.filter(
        Q(sender=request.user, receiver=user_to_chat) |
        Q(sender=user_to_chat, receiver=request.user)
    )

    if after_timestamp:
        try:
            after_datetime = parse_datetime(after_timestamp)
            if after_datetime:
                messages_query = messages_query.filter(timestamp__gt=after_datetime)
            else:
                # If parsing fails, use a default time (e.g., 1 minute ago)
                messages_query = messages_query.filter(timestamp__gt=timezone.now() - timezone.timedelta(minutes=1))
        except ValueError:
            # If parsing fails, use a default time (e.g., 1 minute ago)
            messages_query = messages_query.filter(timestamp__gt=timezone.now() - timezone.timedelta(minutes=1))

    messages = messages_query.order_by('timestamp')
    
    message_list = [{
        'sender': message.sender.username,
        'content': message.content,
        'timestamp': message.timestamp.isoformat(),
    } for message in messages]
    
    return JsonResponse(message_list, safe=False)