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
from django.db.models import Q, Max, Subquery, OuterRef
from django.db import transaction

User = get_user_model()





@login_required
def chat_view(request, username=None):
    current_user = request.user
    users = User.objects.exclude(id=current_user.id)

    # Get the last message for each conversation
    last_messages = Message.objects.filter(
        Q(sender=current_user, receiver=OuterRef('pk')) |
        Q(sender=OuterRef('pk'), receiver=current_user)
    ).order_by('-timestamp')

    users = users.annotate(
        last_message_content=Subquery(last_messages.values('content')[:1]),
        last_message_timestamp=Subquery(last_messages.values('timestamp')[:1])
    ).order_by('-last_message_timestamp')

    context = {
        'users': users,
    }

    if username:
        user_to_chat = get_object_or_404(User, username=username)
        messages = Message.objects.filter(
            Q(sender=current_user, receiver=user_to_chat) |
            Q(sender=user_to_chat, receiver=current_user)
        ).order_by('timestamp')
        
        context.update({
            'user_to_chat': user_to_chat,
            'messages': messages,
        })

    return render(request, 'chat.html', context)

@login_required
@csrf_exempt
def send_message(request, receiver_username):
    try:
        with transaction.atomic():
            data = json.loads(request.body)
            content = data.get('content')
            
            if not content or not content.strip():
                return JsonResponse({'error': 'Message content is empty'}, status=400)
            
            try:
                receiver = SchoolUser.objects.get(username=receiver_username)
            except SchoolUser.DoesNotExist:
                return JsonResponse({'error': 'Receiver not found'}, status=404)
            
            sender = request.user
            
            message = Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=content,
                status='SENT'
            )
            
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': sender.username,
                    'receiver': receiver.username,
                    'timestamp': message.timestamp.isoformat(),
                    'status': message.status,
                }
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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


def some_view(request):
    user_role = request.user.role  # Fetch user role
    context = {
        'user_role': user_role,
    }
    return render(request, 'your_template.html', context) 