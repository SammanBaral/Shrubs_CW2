
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from userprofile.models import UserProfile
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect, render
from .forms import SignupForm, LoginForm
from item.models import Category, Item, ItemImageGallery
from django.contrib import messages
from userprofile.views import sanitize_backend_input, validate_backend_input
from django.db.models import Avg
from decimal import Decimal

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
            return redirect('/login')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'core/verify_otp.html')


def custom_login(request):
    form = LoginForm(request.POST or None)
    error_message = None
    if request.method == 'POST':
        try:
            raw_username = str(request.POST.get('username', ''))
            raw_password = str(request.POST.get('password', ''))
            # Validate raw input first for XSS/NoSQL
            validate_backend_input(raw_username)
            validate_backend_input(raw_password)
            # Then sanitize
            username = sanitize_backend_input(raw_username)
            password = sanitize_backend_input(raw_password)
            user_qs = User.objects.filter(username=username)
            user = user_qs.first() if user_qs.exists() else None
            # Brute-force protection and lockout logic
            user_profile = None
            if user:
                try:
                    user_profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    user_profile = None
            if user_profile and user_profile.lockout_until:
                if timezone.now() < user_profile.lockout_until:
                    error_message = 'Account locked due to too many failed attempts. Try again later.'
                    return render(request, 'core/login.html', {'form': form, 'error_message': error_message})
                else:
                    user_profile.failed_login_attempts = 0
                    user_profile.lockout_until = None
                    user_profile.save()
            if user is not None:
                from django.contrib.auth import authenticate, login
                user_auth = authenticate(request, username=username, password=password)
                if user_auth is not None:
                    if user_profile:
                        user_profile.failed_login_attempts = 0
                        user_profile.lockout_until = None
                        user_profile.save()
                    login(request, user_auth)
                    from core.models import AuditLog
                    AuditLog.objects.create(
                        user=user_auth,
                        user_role='admin' if user_auth.is_superuser else 'customer',
                        action='LOGIN',
                        entity='User',
                        entity_id=str(user_auth.id),
                        old_value=None,
                        new_value=None,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )
                    return redirect('core:main')
                else:
                    if user_profile:
                        user_profile.failed_login_attempts += 1
                        if user_profile.failed_login_attempts >= 5:
                            user_profile.lockout_until = timezone.now() + timedelta(minutes=15)
                            error_message = 'Account locked for 15 minutes due to too many failed attempts.'
                        else:
                            error_message = f'Invalid username or password. {5 - user_profile.failed_login_attempts} attempts left.'
                        user_profile.save()
                    else:
                        error_message = 'Invalid username or password.'
            else:
                error_message = 'Invalid username or password.'
        except SuspiciousOperation as se:
            error_message = str(se) if str(se) else 'Security error: Malicious or unsafe input detected. Please use valid characters.'
        except Exception as e:
            error_message = f'Unexpected error: {e}'
    return render(request, 'core/login.html', {'form': form, 'error_message': error_message})


def signup(request):
    error_message = None
    form = SignupForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = sanitize_backend_input(str(form.cleaned_data['username']))
            password = sanitize_backend_input(str(form.cleaned_data['password']))
            email = sanitize_backend_input(str(form.cleaned_data['email']))
            try:
                validate_backend_input(username)
                validate_backend_input(password)
                validate_backend_input(email)
                if User.objects.filter(username=username).exists():
                    error_message = 'Username already exists.'
                elif User.objects.filter(email=email).exists():
                    error_message = 'Email already exists.'
                else:
                    user = User.objects.create_user(username=username, password=password, email=email)
                    user.save()
                    # Audit log for signup
                    from core.models import AuditLog
                    AuditLog.objects.create(
                        user=user,
                        user_role='admin' if user.is_superuser else 'customer',
                        action='SIGNUP',
                        entity='User',
                        entity_id=str(user.id),
                        old_value=None,
                        new_value={
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name
                        },
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )
                    return redirect('core:login')
            except SuspiciousOperation as se:
                error_message = str(se)
            except Exception as e:
                error_message = f'Unexpected error: {e}'
    return render(request, 'core/signup.html', {'form': form, 'error_message': error_message})



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