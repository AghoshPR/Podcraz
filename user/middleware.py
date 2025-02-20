from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout

class UserBlockCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            
            protected_paths = ['/checkout/', '/payment/', '/orders/']
            if any(request.path.startswith(path) for path in protected_paths):
                if request.user.status == 'Blocked':
                    
                    logout(request)
                   
                    messages.error(request, "Your account has been blocked. Please contact support for assistance.")
                   
                    return redirect('userlogin')
        
        response = self.get_response(request)
        return response 