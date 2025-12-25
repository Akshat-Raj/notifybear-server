from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import F

from .models import (
    NotificationEvent,
    UserNotificationState,
    InteractionEvent,
    App,
    DailyAggregate,
)

User = get_user_model()


# -------------------------
# Signal: Update App.last_seen when new NotificationEvent created
# -------------------------

@receiver(post_save, sender=NotificationEvent)
def update_app_last_seen(sender, instance, created, **kwargs):
    """
    When a new NotificationEvent is created, update the App's last_seen timestamp.
    This helps track which apps are actively sending notifications.
    """
    if created:
        instance.app.last_seen = timezone.now()
        instance.app.save(update_fields=['last_seen'])


# -------------------------
# Signal: Auto-create UserNotificationState when NotificationEvent created
# -------------------------

@receiver(post_save, sender=NotificationEvent)
def create_user_notification_state(sender, instance, created, **kwargs):
    """
    Automatically create a UserNotificationState for the user
    when a new NotificationEvent is created.
    
    This ensures every notification has a corresponding state entry.
    """
    if created:
        user = instance.app.user
        UserNotificationState.objects.get_or_create(
            user=user,
            notification_event=instance,
            defaults={
                'is_read': False,
                'ml_score': None,  # Will be computed later by ML pipeline
            }
        )


# -------------------------
# Signal: Update UserNotificationState when InteractionEvent created
# -------------------------

@receiver(post_save, sender=InteractionEvent)
def update_state_on_interaction(sender, instance, created, **kwargs):
    """
    When an InteractionEvent is logged, automatically update the
    corresponding UserNotificationState.
    
    - CLICK → mark as opened
    - SWIPE → mark as dismissed
    - EXPAND → mark as read (if not already)
    """
    if not created:
        return  # Only process new interactions
    
    # Get or create the user notification state
    state, state_created = UserNotificationState.objects.get_or_create(
        user=instance.user,
        notification_event=instance.notification_event,
        defaults={'is_read': False}
    )
    
    # Update state based on interaction type
    if instance.interaction_type == InteractionEvent.CLICK:
        if not state.opened_at:
            state.opened_at = instance.timestamp
            state.is_read = True
            state.save(update_fields=['opened_at', 'is_read', 'last_updated'])
    
    elif instance.interaction_type == InteractionEvent.SWIPE:
        if not state.dismissed_at:
            state.dismissed_at = instance.timestamp
            state.save(update_fields=['dismissed_at', 'last_updated'])
    
    elif instance.interaction_type == InteractionEvent.EXPAND:
        if not state.is_read:
            state.is_read = True
            state.save(update_fields=['is_read', 'last_updated'])


# -------------------------
# Signal: Update DailyAggregate when InteractionEvent created
# -------------------------

@receiver(post_save, sender=InteractionEvent)
def update_daily_aggregate_on_interaction(sender, instance, created, **kwargs):
    """
    When an InteractionEvent is logged, update the corresponding DailyAggregate.
    
    This keeps statistics up-to-date in real-time.
    """
    if not created:
        return
    
    day = instance.timestamp.date()
    app = instance.notification_event.app
    user = instance.user
    
    # Get or create daily aggregate
    aggregate, _ = DailyAggregate.objects.get_or_create(
        user=user,
        app=app,
        day=day,
        defaults={'posts': 0, 'clicks': 0, 'swipes': 0}
    )
    
    # Increment appropriate counter
    if instance.interaction_type == InteractionEvent.CLICK:
        aggregate.clicks = F('clicks') + 1
    elif instance.interaction_type == InteractionEvent.SWIPE:
        aggregate.swipes = F('swipes') + 1
    
    aggregate.save(update_fields=['clicks' if instance.interaction_type == InteractionEvent.CLICK else 'swipes', 'last_updated'])
    
    # Refresh to get actual values (F() expressions don't update in-memory)
    aggregate.refresh_from_db()
    
    # Recalculate open rate
    aggregate.calculate_open_rate()


# -------------------------
# Signal: Update DailyAggregate when NotificationEvent created
# -------------------------

@receiver(post_save, sender=NotificationEvent)
def update_daily_aggregate_on_post(sender, instance, created, **kwargs):
    """
    When a NotificationEvent is created, increment the posts count
    in the corresponding DailyAggregate.
    """
    if not created:
        return
    
    day = instance.post_time.date()
    app = instance.app
    user = instance.app.user
    
    # Get or create daily aggregate
    aggregate, _ = DailyAggregate.objects.get_or_create(
        user=user,
        app=app,
        day=day,
        defaults={'posts': 0, 'clicks': 0, 'swipes': 0}
    )
    
    # Increment posts
    aggregate.posts = F('posts') + 1
    aggregate.save(update_fields=['posts', 'last_updated'])
    
    # Refresh and recalculate open rate
    aggregate.refresh_from_db()
    aggregate.calculate_open_rate()


# -------------------------
# Signal: Prevent modification of immutable NotificationEvent
# -------------------------

@receiver(pre_save, sender=NotificationEvent)
def prevent_notification_event_modification(sender, instance, **kwargs):
    """
    Prevent modification of existing NotificationEvent instances.
    
    NotificationEvents are immutable - once created, they should not be changed.
    This enforces immutability at the signal level.
    """
    if instance.pk:  # If it's an existing object (has a primary key)
        # Get the original instance from database
        try:
            original = NotificationEvent.objects.get(pk=instance.pk)
            
            # Check if any critical fields have changed
            immutable_fields = [
                'app', 'notif_key', 'post_time', 'title', 'text',
                'big_text', 'sub_text', 'channel_id'
            ]
            
            for field in immutable_fields:
                if getattr(instance, field) != getattr(original, field):
                    raise ValueError(
                        f"NotificationEvent is immutable. "
                        f"Cannot modify field '{field}' after creation."
                    )
        except NotificationEvent.DoesNotExist:
            pass  # New object, allow creation


# -------------------------
# Signal: Prevent deletion of InteractionEvent (append-only)
# -------------------------

# Note: Django doesn't have a pre_delete signal that can prevent deletion,
# so we enforce this through model permissions and admin settings instead.
# See admin.py for has_delete_permission override.


# -------------------------
# Optional: ML Score Recalculation Trigger
# -------------------------

@receiver(post_save, sender=UserNotificationState)
def trigger_ml_score_recalculation(sender, instance, created, **kwargs):
    """
    Optional: Trigger ML score recalculation when user state changes.
    
    This is a placeholder for your ML pipeline integration.
    You can implement this to:
    - Queue a background task (Celery)
    - Call an ML service
    - Update scores in batch
    
    For now, it's just a placeholder.
    """
    # TODO: Implement ML scoring pipeline
    # Example:
    # if instance.opened_at and not instance.ml_score:
    #     from .ml_tasks import calculate_notification_score
    #     calculate_notification_score.delay(instance.id)
    pass


# -------------------------
# Signal: Clean up orphaned data (optional)
# -------------------------

@receiver(post_save, sender=UserNotificationState)
def cleanup_old_notifications(sender, instance, **kwargs):
    """
    Optional: Clean up very old notifications to prevent database bloat.
    
    This is disabled by default. Enable if you want automatic cleanup.
    
    Example: Delete notifications older than 90 days that were dismissed.
    """
    # TODO: Implement cleanup logic if needed
    # from datetime import timedelta
    # cutoff = timezone.now() - timedelta(days=90)
    # 
    # if instance.dismissed_at and instance.dismissed_at < cutoff:
    #     instance.delete()
    pass