from django.utils import timezone
from realsproj.models import UserActivity


class UpdateLastActivityMiddleware:
    """
    Middleware to update user's last_activity timestamp on every request.
    This helps track if a user is actively using the system.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                activity, created = UserActivity.objects.get_or_create(user=request.user)
                activity.last_activity = timezone.now()
                activity.save(update_fields=['last_activity'])
            except Exception:
                pass

        response = self.get_response(request)
        return response
