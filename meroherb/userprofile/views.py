from django.core.mail import EmailMessage
from .forms import OTPVerificationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm
from django.contrib import messages
from userprofile.models import UserProfile
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.contrib.admin.models import LogEntry
from django.dispatch import receiver
from core.models import AuditLog
from item.models import Category
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.utils.decorators import method_decorator
import re
from django.core.exceptions import SuspiciousOperation

def sanitize_backend_input(value):
    value = re.sub(r'<script.*?>.*?</script>', '', value, flags=re.IGNORECASE)
    value = re.sub(r'(\$ne|\$eq|\$gt|\$lt|\$regex|\{|\})', '', value, flags=re.IGNORECASE)
    value = re.sub(r'alert\s*\(', '', value, flags=re.IGNORECASE)
    return value

def validate_backend_input(value):
    if re.search(r'script|<|>|alert|\$ne|\{|\}', value, re.IGNORECASE):
        raise SuspiciousOperation('Security error: Malicious input detected.')
    return value

class PasswordHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=255)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

@login_required
def userprofile(request):
    user = request.user

    try:
        user_profile_instance = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile_instance = UserProfile.objects.create(user=user)

    user_profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user_profile_instance)
    password_change_form = PasswordChangeForm(user)

    otp_form = OTPVerificationForm()
    otp_required = False
    error_message = None
    if request.method == 'POST':
        print('POST data:', request.POST)
        if 'user-details-form-submit' in request.POST:
            print('Edit profile form submitted')
            user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile_instance)
            try:
                print('Form valid:', user_profile_form.is_valid())
                print('Form errors:', user_profile_form.errors)
                if user_profile_form.is_valid():
                    # Sanitize and validate all fields
                    cleaned = user_profile_form.cleaned_data
                    print('Cleaned data:', cleaned)
                    for key in cleaned:
                        cleaned[key] = sanitize_backend_input(str(cleaned[key]))
                        validate_backend_input(cleaned[key])
                    old_profile = {
                        'first_name': user_profile_instance.first_name if user_profile_instance else '',
                        'last_name': user_profile_instance.last_name if user_profile_instance else '',
                        'email': user_profile_instance.email if user_profile_instance else '',
                        'contact_number': user_profile_instance.contact_number if user_profile_instance else '',
                        'location': user_profile_instance.location if user_profile_instance else ''
                    }
                    profile = user_profile_form.save(commit=False)
                    print('Profile before save:', profile)
                    profile.first_name = cleaned.get('first_name', profile.first_name)
                    profile.last_name = cleaned.get('last_name', profile.last_name)
                    profile.email = cleaned.get('email', profile.email)
                    profile.contact_number = cleaned.get('contact_number', profile.contact_number)
                    profile.location = cleaned.get('location', profile.location)
                    # Also update User model fields to keep in sync
                    if hasattr(profile, 'user') and profile.user:
                        profile.user.email = profile.email
                        profile.user.first_name = profile.first_name
                        profile.user.last_name = profile.last_name
                        profile.user.save()
                    # If email changed or not verified, generate OTP and send email
                    otp_needed = not profile.is_email_verified or (user_profile_instance and profile.email != user_profile_instance.email)
                    print('OTP needed:', otp_needed)
                    if otp_needed:
                        import random
                        otp = str(random.randint(100000, 999999))
                        profile.email_otp = otp
                        profile.is_email_verified = False
                        from django.conf import settings
                        email = EmailMessage(
                            'Your Email Verification OTP',
                            f'Your OTP is: {otp}',
                            settings.EMAIL_HOST_USER,
                            [profile.email],
                        )
                        email.send(fail_silently=False)
                        messages.info(request, 'OTP sent to your email. Please verify.')
                        print('Saving profile with OTP...')
                        profile.save()
                        # Audit log for profile update
                        from core.models import AuditLog
                        try:
                            log = AuditLog.objects.create(
                                user=request.user,
                                user_role='admin' if request.user.is_superuser else 'customer',
                                action='UPDATE_PROFILE',
                                entity='UserProfile',
                                entity_id=str(profile.id),
                                old_value=old_profile,
                                new_value={
                                    'first_name': profile.first_name,
                                    'last_name': profile.last_name,
                                    'email': profile.email,
                                    'contact_number': profile.contact_number,
                                    'location': profile.location
                                },
                                ip_address=request.META.get('REMOTE_ADDR'),
                                user_agent=request.META.get('HTTP_USER_AGENT')
                            )
                            print('AuditLog created:', log)
                        except Exception as log_error:
                            print('AuditLog creation failed:', log_error)
                        return render(request, 'userprofile/otp_verify.html', {'otp_form': otp_form, 'user': user, 'error_message': error_message})
                    else:
                        print('Saving profile...')
                        profile.save()
                        messages.success(request, 'User details updated successfully.')
                        # Audit log for profile update
                        from core.models import AuditLog
                        AuditLog.objects.create(
                            user=request.user,
                            user_role='admin' if request.user.is_superuser else 'customer',
                            action='UPDATE_PROFILE',
                            entity='UserProfile',
                            entity_id=str(profile.id),
                            old_value=old_profile,
                            new_value={
                                'first_name': profile.first_name,
                                'last_name': profile.last_name,
                                'email': profile.email,
                                'contact_number': profile.contact_number,
                                'location': profile.location
                            },
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT')
                        )
                        messages.success(request, 'User details updated successfully.')
            except SuspiciousOperation as se:
                error_message = str(se)
                return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form, 'error_message': error_message})
            except Exception as e:
                print('Exception in profile update:', e)
                error_message = 'An unexpected error occurred while updating your profile.'
                return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form, 'error_message': error_message})
    if request.method == 'POST':
        print('POST data:', request.POST)
        if 'user-details-form-submit' in request.POST:
            print('Edit profile form submitted')
            user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile_instance)
            try:
                print('Form valid:', user_profile_form.is_valid())
                print('Form errors:', user_profile_form.errors)
                if user_profile_form.is_valid():
                    # Sanitize and validate all fields
                    cleaned = user_profile_form.cleaned_data
                    print('Cleaned data:', cleaned)
                    for key in cleaned:
                        cleaned[key] = sanitize_backend_input(str(cleaned[key]))
                        validate_backend_input(cleaned[key])
                    old_profile = {
                        'first_name': user_profile_instance.first_name if user_profile_instance else '',
                        'last_name': user_profile_instance.last_name if user_profile_instance else '',
                        'email': user_profile_instance.email if user_profile_instance else '',
                        'contact_number': user_profile_instance.contact_number if user_profile_instance else '',
                        'location': user_profile_instance.location if user_profile_instance else ''
                    }
                    profile = user_profile_form.save(commit=False)
                    print('Profile before save:', profile)
                    profile.first_name = cleaned.get('first_name', profile.first_name)
                    profile.last_name = cleaned.get('last_name', profile.last_name)
                    profile.email = cleaned.get('email', profile.email)
                    profile.contact_number = cleaned.get('contact_number', profile.contact_number)
                    profile.location = cleaned.get('location', profile.location)
                    # Also update User model fields to keep in sync
                    if hasattr(profile, 'user') and profile.user:
                        profile.user.email = profile.email
                        profile.user.first_name = profile.first_name
                        profile.user.last_name = profile.last_name
                        profile.user.save()
                    # If email changed or not verified, generate OTP and send email
                    otp_needed = not profile.is_email_verified or (user_profile_instance and profile.email != user_profile_instance.email)
                    print('OTP needed:', otp_needed)
                    if otp_needed:
                        import random
                        otp = str(random.randint(100000, 999999))
                        profile.email_otp = otp
                        profile.is_email_verified = False
                        from django.conf import settings
                        email = EmailMessage(
                            'Your Email Verification OTP',
                            f'Your OTP is: {otp}',
                            settings.EMAIL_HOST_USER,
                            [profile.email],
                        )
                        email.send(fail_silently=False)
                        messages.info(request, 'OTP sent to your email. Please verify.')
                        print('Saving profile with OTP...')
                        profile.save()
                        # Audit log for profile update
                        from core.models import AuditLog
                        try:
                            log = AuditLog.objects.create(
                                user=request.user,
                                user_role='admin' if request.user.is_superuser else 'customer',
                                action='UPDATE_PROFILE',
                                entity='UserProfile',
                                entity_id=str(profile.id),
                                old_value=old_profile,
                                new_value={
                                    'first_name': profile.first_name,
                                    'last_name': profile.last_name,
                                    'email': profile.email,
                                    'contact_number': profile.contact_number,
                                    'location': profile.location
                                },
                                ip_address=request.META.get('REMOTE_ADDR'),
                                user_agent=request.META.get('HTTP_USER_AGENT')
                            )
                            print('AuditLog created:', log)
                        except Exception as log_error:
                            print('AuditLog creation failed:', log_error)
                        return render(request, 'userprofile/otp_verify.html', {'otp_form': otp_form, 'user': user, 'error_message': error_message})
                    else:
                        print('Saving profile...')
                        profile.save()
                        messages.success(request, 'User details updated successfully.')
                        # Audit log for profile update
                        from core.models import AuditLog
                        AuditLog.objects.create(
                            user=request.user,
                            user_role='admin' if request.user.is_superuser else 'customer',
                            action='UPDATE_PROFILE',
                            entity='UserProfile',
                            entity_id=str(profile.id),
                            old_value=old_profile,
                            new_value={
                                'first_name': profile.first_name,
                                'last_name': profile.last_name,
                                'email': profile.email,
                                'contact_number': profile.contact_number,
                                'location': profile.location
                            },
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT')
                        )
                        messages.success(request, 'User details updated successfully.')
            except SuspiciousOperation as se:
                error_message = str(se)
            except Exception as e:
                print('Exception in profile update:', e)
                error_message = 'An unexpected error occurred while updating your profile.'
                if otp_form.is_valid():
                    otp_input = sanitize_backend_input(otp_form.cleaned_data['otp'])
                    validate_backend_input(otp_input)
                    user_profile_instance = UserProfile.objects.get(user=user)
                    if user_profile_instance.email_otp == otp_input:
                        user_profile_instance.is_email_verified = True
                        user_profile_instance.email_otp = ''
                        user_profile_instance.save()
                        # Audit log for email verification
                        from core.models import AuditLog
                        AuditLog.objects.create(
                            user=request.user,
                            user_role='admin' if request.user.is_superuser else 'customer',
                            action='VERIFY_EMAIL',
                            entity='UserProfile',
                            entity_id=str(user_profile_instance.id),
                            old_value=None,
                            new_value={'is_email_verified': True},
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT')
                        )
                        messages.success(request, 'Email verified successfully!')
                        return redirect('userprofile:userprofile')
                    else:
                        # Audit log for failed email verification
                        from core.models import AuditLog
                        AuditLog.objects.create(
                            user=request.user,
                            user_role='admin' if request.user.is_superuser else 'customer',
                            action='FAILED_VERIFY_EMAIL',
                            entity='UserProfile',
                            entity_id=str(user_profile_instance.id),
                            old_value=None,
                            new_value={'attempted_otp': otp_input},
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT')
                        )
                        messages.error(request, 'Invalid OTP. Please try again.')
                        return render(request, 'userprofile/otp_verify.html', {'otp_form': otp_form, 'user': user, 'error_message': error_message})
            except SuspiciousOperation as se:
                error_message = str(se)
                return render(request, 'userprofile/otp_verify.html', {'otp_form': otp_form, 'user': user, 'error_message': error_message})
        elif 'password-change-form-submit' in request.POST:
            print('Change password form submitted')
            try:
                password_change_form = PasswordChangeForm(user, request.POST)
                print('Form valid:', password_change_form.is_valid())
                print('Form errors:', password_change_form.errors)
                # Password expiry check
                last_pw = PasswordHistory.objects.filter(user=user).order_by('-changed_at').first()
                password_expired = False
                if last_pw and (timezone.now() - last_pw.changed_at).days > 30:
                    password_expired = True
                    messages.error(request, 'Your password has expired. Please set a new password.')
                if password_change_form.is_valid():
                    new_password = sanitize_backend_input(password_change_form.cleaned_data['new_password1'])
                    validate_backend_input(new_password)
                    from django.contrib.auth.hashers import check_password, make_password
                    last_passwords = PasswordHistory.objects.filter(user=user).order_by('-changed_at')[:3]
                    reused = False
                    # Check previous passwords
                    for pw in last_passwords:
                        if check_password(new_password, pw.password):
                            password_change_form.add_error('new_password2', 'You cannot reuse your last 3 passwords.')
                            reused = True
                    # Check current password
                    if check_password(new_password, user.password):
                        password_change_form.add_error('new_password2', 'You cannot reuse your current password.')
                        reused = True
                    if reused:
                        return render(request, 'userprofile/userprofile.html', {
                            'user': user,
                            'user_profile_form': user_profile_form,
                            'password_change_form': password_change_form,
                            'error_message': error_message,
                            'password_expired': password_expired
                        })
                    password_change_form.save()
                    PasswordHistory.objects.create(user=user, password=make_password(new_password))
                    # Keep only last 3 passwords
                    old_pw = PasswordHistory.objects.filter(user=user).order_by('-changed_at')[3:]
                    for pw in old_pw:
                        pw.delete()
                    from core.models import AuditLog
                    AuditLog.objects.create(
                        user=request.user,
                        user_role='admin' if request.user.is_superuser else 'customer',
                        action='CHANGE_PASSWORD',
                        entity='User',
                        entity_id=str(request.user.id),
                        old_value=None,
                        new_value=None,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )
                    messages.success(request, 'Password changed successfully.')
                    return redirect('userprofile:userprofile')
                else:
                    # Show errors in frontend
                    return render(request, 'userprofile/userprofile.html', {
                        'user': user,
                        'user_profile_form': user_profile_form,
                        'password_change_form': password_change_form,
                        'error_message': error_message,
                        'password_expired': password_expired
                    })
            except SuspiciousOperation as se:
                print('SuspiciousOperation:', se)
                error_message = str(se)
                return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form, 'error_message': error_message})
            except ValidationError as e:
                print('ValidationError:', e)
                messages.error(request, f'Error changing password: {e}')
                return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form, 'error_message': error_message})
            except Exception as e:
                print('Exception:', e)
                messages.error(request, f'An unexpected error occurred: {e}')
                return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form, 'error_message': error_message})
    else:
        user_profile_form = UserProfileForm(instance=user_profile_instance)
        password_change_form = PasswordChangeForm(request.user)

    return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form, 'error_message': error_message})

# ------------------ CATEGORY CRUD VIEWS WITH AUDIT LOGGING ------------------
from core.models import AuditLog
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def create_category(request):
    error_message = None
    try:
        name = request.POST.get('name')
        description = request.POST.get('description')
        name = sanitize_backend_input(str(name))
        description = sanitize_backend_input(str(description))
        validate_backend_input(name)
        validate_backend_input(description)
        category = Category.objects.create(name=name, description=description)
        AuditLog.objects.create(
            user=request.user,
            user_role='admin' if request.user.is_superuser else 'customer',
            action='CREATE_CATEGORY',
            entity='Category',
            entity_id=str(category.id),
            old_value=None,
            new_value={'name': name, 'description': description},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        return HttpResponseRedirect(reverse('dashboard:category_list'))
    except SuspiciousOperation as se:
        error_message = str(se)
        return render(request, 'dashboard/category_edit.html', {'error_message': error_message})

@login_required
def update_category(request, category_id):
    category = Category.objects.get(id=category_id)
    old_value = {'name': category.name, 'description': category.description}
    error_message = None
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            name = sanitize_backend_input(str(name))
            description = sanitize_backend_input(str(description))
            validate_backend_input(name)
            validate_backend_input(description)
            category.name = name
            category.description = description
            category.save()
            AuditLog.objects.create(
                user=request.user,
                user_role='admin' if request.user.is_superuser else 'customer',
                action='UPDATE_CATEGORY',
                entity='Category',
                entity_id=str(category.id),
                old_value=old_value,
                new_value={'name': name, 'description': description},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            return HttpResponseRedirect(reverse('dashboard:category_list'))
        except SuspiciousOperation as se:
            error_message = str(se)
            return render(request, 'dashboard/category_edit.html', {'category': category, 'error_message': error_message})
    return render(request, 'dashboard/category_edit.html', {'category': category, 'error_message': error_message})

@login_required
def delete_category(request, category_id):
    category = Category.objects.get(id=category_id)
    old_value = {'name': category.name, 'description': category.description}
    error_message = None
    if request.method == 'POST':
        try:
            # Optionally validate category name/description if present in POST
            name = request.POST.get('name', category.name)
            description = request.POST.get('description', category.description)
            name = sanitize_backend_input(str(name))
            description = sanitize_backend_input(str(description))
            validate_backend_input(name)
            validate_backend_input(description)
            category.delete()
            AuditLog.objects.create(
                user=request.user,
                user_role='admin' if request.user.is_superuser else 'customer',
                action='DELETE_CATEGORY',
                entity='Category',
                entity_id=str(category_id),
                old_value=old_value,
                new_value=None,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            return HttpResponseRedirect(reverse('dashboard:category_list'))
        except SuspiciousOperation as se:
            error_message = str(se)
            return render(request, 'dashboard/category_confirm_delete.html', {'category': category, 'error_message': error_message})
    return render(request, 'dashboard/category_confirm_delete.html', {'category': category, 'error_message': error_message})

@receiver(post_save, sender=LogEntry)
def admin_action_log(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.user,
            user_role='admin',
            action=instance.get_action_flag_display(),
            entity=instance.content_type.model,
            entity_id=str(instance.object_id),
            old_value=None,  # Optionally fetch previous state if needed
            new_value={'change_message': instance.change_message},
            ip_address=None,  # Not available in LogEntry
            user_agent=None  # Not available in LogEntry
        )

@receiver(post_delete, sender=LogEntry)
def admin_action_delete_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.user,
        user_role='admin',
        action='DELETE',
        entity=instance.content_type.model,
        entity_id=str(instance.object_id),
        old_value=None,
        new_value=None,
        ip_address=None,
        user_agent=None
    )

# Password expiry and reuse prevention logic
@login_required
def change_password(request):
    user = request.user
    password_change_form = PasswordChangeForm(user, request.POST or None)
    password_expired = False
    password_history = PasswordHistory.objects.filter(user=user)
    last_change = password_history.first()
    if last_change and (timezone.now() - last_change.changed_at).days > 90:
        password_expired = True
    if request.method == 'POST':
        if password_change_form.is_valid():
            new_password = password_change_form.cleaned_data['new_password1']
            # Prevent password reuse
            reused = any(check_password(new_password, ph.password) for ph in password_history)
            if reused:
                messages.error(request, 'You cannot reuse a previous password.')
            else:
                user.set_password(new_password)
                user.save()
                PasswordHistory.objects.create(user=user, password=user.password)
                messages.success(request, 'Password changed successfully.')
                # Audit log for password change
                AuditLog.objects.create(
                    user=request.user,
                    user_role='admin' if request.user.is_superuser else 'customer',
                    action='CHANGE_PASSWORD',
                    entity='User',
                    entity_id=str(request.user.id),
                    old_value=None,
                    new_value=None,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                return redirect('userprofile:userprofile')
    return render(request, 'userprofile/change_password.html', {
        'form': password_change_form,
        'password_expired': password_expired,
        'password_history': password_history
    })

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = SetPasswordForm

    @method_decorator(login_required, name='dispatch')
    def form_valid(self, form):
        user = self.get_user()
        password_history = PasswordHistory.objects.filter(user=user)
        new_password = form.cleaned_data['new_password1']
        # Prevent password reuse
        reused = any(check_password(new_password, ph.password) for ph in password_history)
        if reused:
            form.add_error('new_password1', 'You cannot reuse a previous password.')
            return self.form_invalid(form)
        # Enforce password expiry
        last_change = password_history.first()
        if last_change and (timezone.now() - last_change.changed_at).days > 90:
            # Optionally show expiry message or force change
            pass
        user.set_password(new_password)
        user.save()
        PasswordHistory.objects.create(user=user, password=user.password)
        AuditLog.objects.create(
            user=user,
            user_role='admin' if user.is_superuser else 'customer',
            action='RESET_PASSWORD',
            entity='User',
            entity_id=str(user.id),
            old_value=None,
            new_value=None,
            ip_address=None,
            user_agent=None
        )
        return super().form_valid(form)
