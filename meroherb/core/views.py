# Khalti callback view to verify payment
def khalti_callback(request):
    pidx = request.GET.get('pidx')
    bill_no = request.GET.get('purchase_order_id')
    status = request.GET.get('status')
    # Lookup payment status
    headers = {
        "Authorization": "Key e3c766f8643648e39f2251e90dfe7757",
        "Content-Type": "application/json"
    }
    payload = {"pidx": pidx}
    resp = requests.post("https://khalti.com/api/v2/epayment/lookup/", data=json.dumps(payload), headers=headers)
    resp_data = resp.json()
    if resp.status_code == 200 and resp_data.get("status") == "Completed":
        bill = get_object_or_404(Bill, bill_no=bill_no)
        bill.is_paid = True
        bill.save()
        # Send email to seller
        from django.core.mail import EmailMessage
        seller_email = bill.item.created_by.email
        subject = f'New Bill for Item: {bill.item.name}'
        message = 'Please deliver the Item as soon as possible'
        email = EmailMessage(subject, message, 'herbsbazaar@gmail.com', [seller_email])
        if bill.pdf:
            email.attach_file(bill.pdf.path)
        email.send()
        return redirect('/')
    else:
        return render(request, "core/payment_failed.html", {"error": resp_data.get("detail", "Payment not completed")})
import json
from django.http import HttpResponseRedirect
# Initiate Khalti payment (recommended API flow)
def initiate_khalti_payment(request, bill_no):
    bill = get_object_or_404(Bill, bill_no=bill_no)
    # Convert USD to NPR (default rate: 133)
    usd_to_npr = 133
    npr_amount = int(float(bill.discount_price or bill.total_amount) * usd_to_npr * 100)  # in paisa
    payload = {
        "return_url": request.build_absolute_uri("/khalti/callback/"),
        "website_url": request.build_absolute_uri("/"),
        "amount": npr_amount,
        "purchase_order_id": str(bill.bill_no),
        "purchase_order_name": str(bill.item),
        "customer_info": {
            "name": bill.customer.get_full_name() or bill.customer.username,
            "email": bill.customer.email,
            "phone": bill.contact_info or "9800000000"
        },
        "product_details": [
            {
                "identity": str(bill.item.id),
                "name": bill.item.name,
                "total_price": npr_amount,
                "quantity": bill.quantity,
                "unit_price": npr_amount
            }
        ]
    }
    headers = {
        "Authorization": "Key e3c766f8643648e39f2251e90dfe7757",
        "Content-Type": "application/json"
    }
    resp = requests.post("https://khalti.com/api/v2/epayment/initiate/", data=json.dumps(payload), headers=headers)
    resp_data = resp.json()
    if resp.status_code == 200 and resp_data.get("payment_url"):
        return HttpResponseRedirect(resp_data["payment_url"])
    else:
        return render(request, "core/payment_failed.html", {"error": resp_data.get("detail", "Payment initiation failed")})
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from userprofile.forms import UserProfileForm
from item.models import Bill

@csrf_exempt
def verify_khalti(request):
    import json
    data = json.loads(request.body)
    token = data.get('token')
    amount = data.get('amount')
    bill_id = data.get('bill_id')
    url = "https://khalti.com/api/v2/payment/verify/"
    payload = {
        "token": token,
        "amount": amount
    }
    headers = {
        "Authorization": "Key e3c766f8643648e39f2251e90dfe7757"
    }
    resp = requests.post(url, payload, headers=headers)
    resp_data = resp.json()
    if resp.status_code == 200 and resp_data.get('idx'):
        # Mark bill as paid
        bill = get_object_or_404(Bill, bill_no=bill_id)
        bill.is_paid = True
        bill.save()
        # Send email to seller
        from django.core.mail import EmailMessage
        seller_email = bill.item.created_by.email
        subject = f'New Bill for Item: {bill.item.name}'
        message = 'Please deliver the Item as soon as possible'
        email = EmailMessage(subject, message, 'herbsbazaar@gmail.com', [seller_email])
        if bill.pdf:
            email.attach_file(bill.pdf.path)
        email.send()
        # Redirect to home page after payment
        return JsonResponse({"success": True, "redirect_url": "/"})
    else:
        return JsonResponse({"success": False, "message": "Payment verification failed!"}, status=400)

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
                    # Password expiry enforcement
                    from userprofile.views import PasswordHistory
                    last_pw = PasswordHistory.objects.filter(user=user_auth).order_by('-changed_at').first()
                    password_expired = False
                    if last_pw and (timezone.now() - last_pw.changed_at).days > 30:
                        password_expired = True
                    if password_expired:
                        messages.error(request, 'Your password has expired. Please set a new password.')
                        from userprofile.views import userprofile
                        # Render password change form directly
                        password_change_form = PasswordChangeForm(user_auth)
                        user_profile_instance = None
                        try:
                            user_profile_instance = UserProfile.objects.get(user=user_auth)
                        except UserProfile.DoesNotExist:
                            user_profile_instance = UserProfile.objects.create(user=user_auth)
                        user_profile_form = UserProfileForm(instance=user_profile_instance)
                        return render(request, 'userprofile/userprofile.html', {
                            'user': user_auth,
                            'user_profile_form': user_profile_form,
                            'password_change_form': password_change_form,
                            'error_message': 'Your password has expired. Please set a new password.',
                            'password_expired': True
                        })
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