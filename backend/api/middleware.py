import redis
from django.conf import settings
from django.utils import timezone

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.r = None

    def __call__(self, request):
        response = self.get_response(request)

        user_id = None
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user_id = request.user.id

        # Gravar atividade no Redis apenas se o usuário estiver autenticado
        if user_id:
            try:
                if not self.r:
                    redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
                    self.r = redis.Redis.from_url(redis_url)
                
                key = f"user_active_{user_id}"
                self.r.setex(key, 60, int(timezone.now().timestamp()))
            except Exception as e:
                print(f"Error recording user activity in Redis: {e}")

        return response

class ClearSerializerCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from api.serializers import clear_local_cache
        clear_local_cache()
        try:
            response = self.get_response(request)
        finally:
            clear_local_cache()
        return response

