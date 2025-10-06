from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import UserActivity

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    activity, created = UserActivity.objects.get_or_create(user=user)
    user.last_login = timezone.now()
    user.save()

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    if user.is_authenticated:
        activity, created = UserActivity.objects.get_or_create(user=user)
        activity.last_logout = timezone.now()
        activity.save()
