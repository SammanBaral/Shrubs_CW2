from django.core.mail import EmailMessage
from .forms import OTPVerificationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserProfileForm
from django.contrib import messages
from userprofile.models import UserProfile
from django.core.exceptions import ValidationError

@login_required
def userprofile(request):
    user = request.user

    try:
        user_profile_instance = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile_instance = None

    user_profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user_profile_instance)
    password_change_form = PasswordChangeForm(user)

    otp_form = OTPVerificationForm()
    otp_required = False
    if request.method == 'POST':
        if 'user-details-form-submit' in request.POST:
            user_profile_form = UserProfileForm(request.POST, instance=user)
            try:
                if user_profile_form.is_valid():
                    profile = user_profile_form.save(commit=False)
                    # If email changed or not verified, generate OTP and send email
                    if not profile.is_email_verified or (user_profile_instance and profile.email != user_profile_instance.email):
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
                        profile.save()
                        return render(request, 'userprofile/otp_verify.html', {'otp_form': otp_form, 'user': user})
                    else:
                        profile.save()
                        messages.success(request, 'User details updated successfully.')
            except ValidationError as e:
                messages.error(request, f'Error updating user details: {e}')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {e}')
        elif 'otp-verify-form-submit' in request.POST:
            otp_form = OTPVerificationForm(request.POST)
            if otp_form.is_valid():
                otp_input = otp_form.cleaned_data['otp']
                user_profile_instance = UserProfile.objects.get(user=user)
                if user_profile_instance.email_otp == otp_input:
                    user_profile_instance.is_email_verified = True
                    user_profile_instance.email_otp = ''
                    user_profile_instance.save()
                    messages.success(request, 'Email verified successfully!')
                    return redirect('userprofile:userprofile')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    return render(request, 'userprofile/otp_verify.html', {'otp_form': otp_form, 'user': user})

        elif 'password-change-form-submit' in request.POST:
            try:
                password_change_form = PasswordChangeForm(user, request.POST)
                if password_change_form.is_valid():
                    password_change_form.save()
                    messages.success(request, 'Password changed successfully.')
            except ValidationError as e:
                messages.error(request, f'Error changing password: {e}')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {e}')

        return redirect('userprofile:userprofile')
    else:
        user_profile_form = UserProfileForm(instance=user_profile_instance)
        password_change_form = PasswordChangeForm(request.user)

    return render(request, 'userprofile/userprofile.html', {'user': user, 'user_profile_form': user_profile_form, 'password_change_form': password_change_form})
