class SSLRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.is_secure() and not request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            from django.shortcuts import redirect
            url = request.build_absolute_uri(request.get_full_path())
            secure_url = url.replace('http://', 'https://', 1)
            return redirect(secure_url)
        return self.get_response(request)
