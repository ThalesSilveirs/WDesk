import redis
from django.conf import settings
from django.utils import timezone

# Initialize Redis client from Celery broker URL
redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
r = redis.Redis.from_url(redis_url)

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            # Mark user as active for 60 seconds (since dashboard polls every 10s)
            key = f"user_active_{request.user.id}"
            r.setex(key, 60, int(timezone.now().timestamp()))
        return self.get_response(request)
