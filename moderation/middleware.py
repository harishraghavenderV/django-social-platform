from django.http import Http404
from django.contrib.auth.models import User
from .models import Block

class BlockMiddleware:
    """Middleware to attach block lists to request and restrict access to blocked profiles."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get IDs of users this user has blocked and who blocked this user
            blocked_ids = Block.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
            blocked_by_ids = Block.objects.filter(blocked=request.user).values_list('blocker_id', flat=True)
            
            # Store sets on request object
            request.blocked_user_ids = set(blocked_ids)
            request.blocked_by_user_ids = set(blocked_by_ids)
            request.all_blocked_ids = request.blocked_user_ids.union(request.blocked_by_user_ids)
            
            # Simple URL inspection: raise 404 if trying to access profile of blocked user
            path_parts = [p for p in request.path.strip('/').split('/') if p]
            if len(path_parts) >= 2 and path_parts[0] == 'profile':
                username = path_parts[1]
                target_user = User.objects.filter(username=username).first()
                if target_user and (target_user.id in request.all_blocked_ids):
                    raise Http404("Profile not found or blocked.")
        else:
            request.blocked_user_ids = set()
            request.blocked_by_user_ids = set()
            request.all_blocked_ids = set()

        response = self.get_response(request)
        return response
