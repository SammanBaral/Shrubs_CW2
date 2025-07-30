from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from userprofile.models import UserProfile
def verify_otp(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending registration found.')
        return redirect('/signup/')
    user_profile = UserProfile.objects.filter(user_id=user_id).first()
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if user_profile and user_profile.email_otp == otp_input:
            user_profile.is_email_verified = True
            user_profile.email_otp = ''
            user_profile.save()
            del request.session['pending_user_id']
            messages.success(request, 'Email verified successfully! You can now log in.')
            return redirect('/login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'core/verify_otp.html')
from django.shortcuts import redirect, render
from .forms import SignupForm, LoginForm
from item.models import Category, Item, ItemImageGallery
from django.contrib import messages

def custom_login(request):
    import sys
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        username = request.POST.get('username')
        user_qs = User.objects.filter(username=username)
        user = user_qs.first() if user_qs.exists() else None
        profile = None
        if user:
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                pass
        if profile:
            print(f"DEBUG: Username={username}, Attempts={profile.failed_login_attempts}, LockoutUntil={profile.lockout_until}", file=sys.stderr)
        # Check lockout before validating form
        if profile and profile.lockout_until and profile.lockout_until > timezone.now():
            messages.error(request, 'Account is locked due to multiple failed login attempts. Please try again later.')
            return render(request, 'core/login.html', {'form': form})
        # Only validate form if not locked
        if form.is_valid():
            if profile:
                profile.failed_login_attempts = 0
                profile.lockout_until = None
                profile.save()
            from django.contrib.auth import login
            login(request, form.get_user())
            return redirect('/main/')
        else:
            if profile:
                profile.failed_login_attempts += 1
                if profile.failed_login_attempts >= 5:
                    profile.lockout_until = timezone.now() + timedelta(minutes=15)
                    profile.failed_login_attempts = 0
                    messages.error(request, 'Account locked due to multiple failed login attempts. Try again in 15 minutes.')
                profile.save()
                print(f"DEBUG: After fail, Attempts={profile.failed_login_attempts}, LockoutUntil={profile.lockout_until}", file=sys.stderr)
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})
from item.decorators import unauthenticated_user
from django.db.models import Avg
from decimal import Decimal
from userprofile.models import UserProfile  # Import your UserProfile model

@unauthenticated_user
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Create User instance
            user = form.save()

            # Create UserProfile instance
            import random
            from django.core.mail import EmailMessage
            from django.conf import settings
            otp = str(random.randint(100000, 999999))
            user_profile = UserProfile.objects.create(
                user=user,
                username=form.cleaned_data['username'],
                contact_number=form.cleaned_data['contact_number'],
                location=form.cleaned_data['location'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                email_otp=otp,
                is_email_verified=False,
            )
            user_profile.photo = 'default_user.png'
            user_profile.save()

            email = EmailMessage(
                'Your Email Verification OTP',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [user_profile.email],
            )
            email.send(fail_silently=False)
            messages.info(request, 'OTP sent to your email. Please verify.')
            request.session['pending_user_id'] = user.id
            return redirect('/verify-otp/')
    else:
        form = SignupForm()

    return render(request, 'core/signup.html', {'form': form})



def mainpage(request):
    categories = Category.objects.all()


    new_products = Item.objects.annotate(
        avg_rating=Avg('review__rating')
    ).order_by('-created_at')[:12]

    for category in categories:
        category.name = category.name.upper()

    new_products_with_images = []
    for product in new_products:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        new_products_with_images.append(product_data)


    best_selling = Item.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:4]
    for product in best_selling:
        if product.discount > 0:
            discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
            product.discounted_price = discounted_price

    best_selling_with_images = []
    for product in best_selling:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        best_selling_with_images.append(product_data)



    latest_products = Item.objects.order_by('-created_at')[:4]

    for product in latest_products:
        if product.discount > 0:
            discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
            product.discounted_price = discounted_price


    latest_products_with_images = []
    for product in latest_products:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        latest_products_with_images.append(product_data)


    deal_day = Item.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:2]
    for product in deal_day:
        if product.discount > 0:
            discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
            product.discounted_price = discounted_price

    deal_day_with_images = []
    for product in deal_day:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        deal_day_with_images.append(product_data)


    top_rated = Item.objects.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')[:4]

    for product in top_rated:
        if product.discount > 0:
            discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
            product.discounted_price = discounted_price

    top_rated_with_images = []
    for product in top_rated:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        top_rated_with_images.append(product_data)


    trending_products = Item.objects.order_by('price')[:4]

    for product in trending_products:
        if product.discount > 0:
            discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
            product.discounted_price = discounted_price
            
    trending_products_with_images = []
    for product in trending_products:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        trending_products_with_images.append(product_data)

    #calculating discount and adding the data to the item discount field in model 
    for product in new_products:
        if product.discount > 0:
            discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
            product.discounted_price = discounted_price
    
    return render(request, 'core/main.html', {
        
        'deals': deal_day,
        'categories': categories,
        'deal_day_with_images': deal_day_with_images,
        'trending_products_with_images':trending_products_with_images,
        'new_products_with_images':new_products_with_images,
        'best_selling_with_images': best_selling_with_images,
        'latest_product_with_images': latest_products_with_images,
        'top_rated_with_images':top_rated_with_images,


    })