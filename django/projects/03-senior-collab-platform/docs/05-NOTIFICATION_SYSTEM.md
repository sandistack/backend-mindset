# 🔔 Step 5: Notification System

**Waktu:** 6-8 jam  
**Prerequisite:** Step 4 selesai

---

## 🎯 Tujuan

- In-app notifications
- Real-time delivery via WebSocket
- Push notifications (Web Push/FCM)
- Email notifications
- Notification preferences

---

## 📋 Notification Types

```
MENTION        - @mentioned in document/comment
MESSAGE        - New message in channel
COMMENT        - Comment on your document
INVITE         - Invited to workspace
TASK           - Task assigned/updated
DOCUMENT       - Document shared/updated
DAILY_DIGEST   - Daily activity summary
```

---

## 📋 Tasks

### 5.1 Notification Model

**Di `apps/notifications/models.py`:**

```python
from django.db import models
from apps.core.models import BaseModel
from django.conf import settings

class Notification(BaseModel):
    TYPE_CHOICES = [
        ('mention', 'Mention'),
        ('message', 'Message'),
        ('comment', 'Comment'),
        ('invite', 'Invite'),
        ('task', 'Task'),
        ('document', 'Document'),
        ('daily_digest', 'Daily Digest'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    data = models.JSONField(default=dict)
    
    # Reference to related object
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    
    # Actor (who triggered the notification)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='triggered_notifications'
    )
    
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read_at']),
            models.Index(fields=['user', 'type', 'created_at']),
        ]
    
    @property
    def is_read(self):
        return self.read_at is not None


class NotificationPreference(BaseModel):
    """User notification preferences"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # In-app
    in_app_enabled = models.BooleanField(default=True)
    
    # Push
    push_enabled = models.BooleanField(default=True)
    
    # Email
    email_enabled = models.BooleanField(default=True)
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('hourly', 'Hourly Digest'),
            ('daily', 'Daily Digest'),
            ('never', 'Never'),
        ],
        default='instant'
    )
    
    # Type-specific settings
    mention_enabled = models.BooleanField(default=True)
    message_enabled = models.BooleanField(default=True)
    comment_enabled = models.BooleanField(default=True)
    task_enabled = models.BooleanField(default=True)


class PushSubscription(BaseModel):
    """Web Push subscription"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    endpoint = models.URLField()
    p256dh_key = models.TextField()
    auth_key = models.TextField()
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['user', 'endpoint']
```

### 5.2 Notification Service

**Buat `apps/notifications/services.py`:**

```python
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, NotificationPreference, PushSubscription
from .serializers import NotificationSerializer
from .tasks import send_push_notification, send_email_notification

class NotificationService:
    
    @classmethod
    def create(cls, user, notification_type, title, body='', data=None, actor=None, target_type='', target_id=None):
        """Create and deliver notification"""
        
        # Check preferences
        prefs = cls.get_preferences(user)
        
        if not prefs.in_app_enabled:
            return None
        
        # Check type-specific preference
        type_enabled_field = f'{notification_type}_enabled'
        if hasattr(prefs, type_enabled_field) and not getattr(prefs, type_enabled_field):
            return None
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            body=body,
            data=data or {},
            actor=actor,
            target_type=target_type,
            target_id=target_id
        )
        
        # Deliver real-time
        cls.deliver_realtime(notification)
        
        # Send push if enabled
        if prefs.push_enabled:
            send_push_notification.delay(notification.id)
        
        # Send email based on frequency
        if prefs.email_enabled and prefs.email_frequency == 'instant':
            send_email_notification.delay(notification.id)
        
        return notification
    
    @classmethod
    def deliver_realtime(cls, notification):
        """Send notification via WebSocket"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'notifications_{notification.user_id}',
            {
                'type': 'notification',
                'data': NotificationSerializer(notification).data
            }
        )
    
    @classmethod
    def mark_read(cls, notification_id, user):
        """Mark notification as read"""
        Notification.objects.filter(
            id=notification_id,
            user=user
        ).update(read_at=timezone.now())
    
    @classmethod
    def mark_all_read(cls, user):
        """Mark all notifications as read"""
        Notification.objects.filter(
            user=user,
            read_at__isnull=True
        ).update(read_at=timezone.now())
    
    @classmethod
    def get_unread_count(cls, user):
        """Get unread notification count"""
        from django.core.cache import cache
        
        cache_key = f'notification_unread_{user.id}'
        count = cache.get(cache_key)
        
        if count is None:
            count = Notification.objects.filter(
                user=user,
                read_at__isnull=True
            ).count()
            cache.set(cache_key, count, 60)  # Cache for 1 minute
        
        return count
    
    @classmethod
    def get_preferences(cls, user):
        """Get or create user preferences"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        return prefs
    
    # Notification creators for specific events
    @classmethod
    def notify_mention(cls, mentioned_user, actor, document):
        """Notify user about mention"""
        return cls.create(
            user=mentioned_user,
            notification_type='mention',
            title=f'{actor.name} mentioned you',
            body=f'in "{document.title}"',
            data={'document_id': str(document.id)},
            actor=actor,
            target_type='document',
            target_id=document.id
        )
    
    @classmethod
    def notify_message(cls, user, channel, message, actor):
        """Notify about new message"""
        return cls.create(
            user=user,
            notification_type='message',
            title=f'New message in #{channel.name}',
            body=message.content[:100],
            data={'channel_id': str(channel.id), 'message_id': str(message.id)},
            actor=actor,
            target_type='message',
            target_id=message.id
        )
    
    @classmethod
    def notify_invite(cls, user, workspace, invited_by):
        """Notify about workspace invite"""
        return cls.create(
            user=user,
            notification_type='invite',
            title=f'You\'ve been invited to {workspace.name}',
            body=f'by {invited_by.name}',
            data={'workspace_id': str(workspace.id)},
            actor=invited_by,
            target_type='workspace',
            target_id=workspace.id
        )
```

### 5.3 Push Notification Service

**Buat `apps/notifications/push_service.py`:**

```python
from pywebpush import webpush, WebPushException
from django.conf import settings
import json

class PushNotificationService:
    
    def __init__(self):
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_claims = {
            'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'
        }
    
    def send(self, notification):
        """Send push notification to all user's subscriptions"""
        subscriptions = PushSubscription.objects.filter(
            user=notification.user
        )
        
        payload = json.dumps({
            'title': notification.title,
            'body': notification.body,
            'icon': '/icon.png',
            'badge': '/badge.png',
            'data': {
                'notification_id': str(notification.id),
                **notification.data
            }
        })
        
        for sub in subscriptions:
            try:
                webpush(
                    subscription_info={
                        'endpoint': sub.endpoint,
                        'keys': {
                            'p256dh': sub.p256dh_key,
                            'auth': sub.auth_key
                        }
                    },
                    data=payload,
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=self.vapid_claims
                )
            except WebPushException as e:
                if e.response.status_code == 410:  # Subscription expired
                    sub.delete()
```

### 5.4 Views

```python
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('actor')[:50]


class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Mark as read on view
        if not instance.read_at:
            NotificationService.mark_read(instance.id, request.user)
        
        return super().retrieve(request, *args, **kwargs)


class MarkReadView(APIView):
    def post(self, request):
        notification_ids = request.data.get('ids', [])
        
        if notification_ids:
            Notification.objects.filter(
                id__in=notification_ids,
                user=request.user
            ).update(read_at=timezone.now())
        else:
            NotificationService.mark_all_read(request.user)
        
        return Response({'status': 'ok'})


class UnreadCountView(APIView):
    def get(self, request):
        count = NotificationService.get_unread_count(request.user)
        return Response({'count': count})


class PushSubscriptionView(APIView):
    def post(self, request):
        """Subscribe to push notifications"""
        PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=request.data['endpoint'],
            defaults={
                'p256dh_key': request.data['keys']['p256dh'],
                'auth_key': request.data['keys']['auth'],
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )
        return Response({'status': 'subscribed'})
    
    def delete(self, request):
        """Unsubscribe from push"""
        endpoint = request.data.get('endpoint')
        PushSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint
        ).delete()
        return Response({'status': 'unsubscribed'})
```

---

## ✅ Checklist

- [ ] Notification model
- [ ] NotificationPreference model
- [ ] PushSubscription model
- [ ] NotificationService
- [ ] Real-time delivery via WebSocket
- [ ] Push notification service
- [ ] Email notification task
- [ ] API endpoints
- [ ] Mark as read functionality
- [ ] Unread count with caching
- [ ] Type-specific notification creators

---

## 🔗 Referensi

- [WEBSOCKET.md](../../../docs/04-advanced/WEBSOCKET.md) - Real-time delivery
- [EMAIL.md](../../../docs/04-advanced/EMAIL.md) - Email notifications
- [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md) - Async tasks

---

## ➡️ Next Step

Lanjut ke [06-FILE_COLLABORATION.md](06-FILE_COLLABORATION.md) - Shared Files
