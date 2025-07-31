from django import forms
from .models import UserProfile

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, label='Enter OTP')
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import UserProfile
from sellerform.models import SellerAccount  # Import your UserProfile model

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'last_name', 'contact_number','location']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Always allow current user's own email
        userprofile_pk = self.instance.pk if self.instance else None
        user_obj = getattr(self.instance, 'user', None)
        user_pk = user_obj.pk if user_obj else None
        # Check for duplicate in UserProfile (excluding self)
        if UserProfile.objects.filter(email=email).exclude(pk=userprofile_pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        # Check for duplicate in User (excluding self)
        from django.contrib.auth.models import User
        if User.objects.filter(email=email).exclude(pk=user_pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        pass

# class BioLocationForm(forms.ModelForm):
#     class Meta:
#         model = SellerAccount
#         fields = ['bio', 'location']