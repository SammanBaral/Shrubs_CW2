
from datetime import timedelta
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib import messages
from .forms import UserProfilePhotoForm
from django.contrib.auth.models import User,Group
from django.db import IntegrityError


def sellerform(request):
    form = UserProfilePhotoForm()  

    if request.method == 'POST':
        username = request.POST.get('username')
        picture=request.FILES.get('image')
        print(username)
        print(picture)

        if(username!=request.user.username):
            messages.error(request, "Invalid Username, Try again")
            return render(request, 'sellerform/sellerform.html', {'form': form})
        
        elif not picture:
            messages.error(request, "Please upload your profile picture")
            return render(request, 'sellerform/sellerform.html', {'form': form})
        
        else:
            # Check if the user exists
            try:
                user = User.objects.get(username=username)
                print(user)
            except User.DoesNotExist:
                # Handle case where user doesn't exist
                messages.error(request, "Invalid Username, Try again")
                return render(request, 'sellerform/sellerform.html', {'form': form})
            
        # Check if the user should be granted seller status
        if user_should_be_seller(user):

            try:
            # Get or create the 'seller' group
                seller_group, created = Group.objects.get_or_create(name='seller')
            # Add user to 'seller' group
                user.groups.add(seller_group)

                form = UserProfilePhotoForm(request.POST, request.FILES)
                if form.is_valid():
                    profile = form.save(commit=False)
                    profile.user = user
                    profile.save()
                    return redirect('core:main')
                else:
                    return render(request, 'sellerform/sellerform.html', {'form': form})
            except IntegrityError:
                messages.error(request,"You already have a seller account")
                return render(request, 'sellerform/sellerform.html', {'form': form})
        else:
            messages.warning(request, "You do not meet the requirements to be a seller")
            return render(request, 'sellerform/sellerform.html', {'form': form})

    return render(request, 'sellerform/sellerform.html', {'form': form})


def user_should_be_seller(user):
    # Example criteria:
    # Check if the user has been active for a certain period (e.g., 30 days)
    # active_threshold = timedelta(days=1)
    # if timezone.now() - user.date_joined < active_threshold:
    #     return False

    # Check if the user has verified their email
    # if not user.email or not user.email_verified:
    #     return False

    # # Check if the user has completed a certain number of orders
    # min_orders_completed = 10
    # user_orders_completed = user.orders.filter(status='completed').count()
    # if user_orders_completed < min_orders_completed:
    #     return False

    # # Add more conditions here based on your application's requirements
    # # ...

    # If all criteria are met, return True
    return True
