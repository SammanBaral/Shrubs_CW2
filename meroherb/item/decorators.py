from django.shortcuts import redirect
from django.http import HttpResponse

#takes the view function above which it will be declared

# using wraped function or decorator type function cause we need to have some verification step so that the function parameter(view_func) will no be executed
def unauthenticated_user(view_func):
    def wrapper_func(request,*args, **kwargs):
        if request.user.is_authenticated:
            return redirect('main')       # if the user is authentictaed the view function will not be executed preventing from loading the page
        else:
            return view_func(request,*args,**kwargs)     # if the user is autheticated the view function below the decorator will be executed 
        
    return wrapper_func    # returns the wrapper function with its action

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.is_authenticated:  # Ensure user is logged in
                group = None
                if request.user.groups.exists():
                    group = request.user.groups.all()[0].name
                    print("User group:", group)
                    print("Allowed roles:", allowed_roles)

                if group in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponse("You are not authorized to view this page, you need to be a seller to view this page")
            else:
                return HttpResponse("Please log in to view this page")

        return wrapper_func

    return decorator
