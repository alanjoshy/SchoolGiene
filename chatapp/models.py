from django.db import models
from django.utils import timezone
from adminapp.models import SchoolUser
from django.contrib.auth import get_user_model# Import SchoolUser from the app where it's defined



class Message(models.Model):
    sender = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']

