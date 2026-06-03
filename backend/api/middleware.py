import redis
from django.conf import settings
from django.utils import timezone

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.r = None

    def __call__(self, request):
        user_id = None
        
        # 1. Try session authentication
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user_id = request.user.id
            
        # 2. Try JWT Bearer token authentication
        else:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                try:
                    from rest_framework_simplejwt.tokens import AccessToken
                    token = auth_header.split(' ')[1]
                    access_token = AccessToken(token)
                    user_id = access_token['user_id']
                except Exception:
                    pass

        # 3. If user is authenticated, record activity in Redis
        if user_id:
            try:
                if not self.r:
                    redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
                    self.r = redis.Redis.from_url(redis_url)
                
                status_key = f"user_status_{user_id}"
                status_bytes = self.r.get(status_key)
                status = status_bytes.decode('utf-8') if status_bytes else None
                
                if status != 'offline':
                    key = f"user_active_{user_id}"
                    self.r.setex(key, 60, int(timezone.now().timestamp()))
            except Exception as e:
                # Catch exceptions to prevent API crashes if Redis is briefly unreachable
                print(f"Error recording user activity in Redis: {e}")

        return self.get_response(request)

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

