# class FilterIPMiddleware(object):
#     # Check if client IP is allowed

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         return self.get_response(request)

#     def process_exception(self, request, exception): 
#         return '' #HttpResponse("in exception")
    
#     def process_request(self, request):
#         print(request.user)
#         allowed_ips = ['192.168.1.1', '123.123.123.123'] # Authorized ip's
#         ip = request.META.get('REMOTE_ADDR') # Get client IP
#         if ip not in allowed_ips:
#             raise 'Http403' # If user is not allowed raise Error 
#        # If IP is allowed we don't do anything
#         return None