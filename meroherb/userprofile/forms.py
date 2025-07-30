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
        if UserProfile.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    class Meta:
        pass

# class BioLocationForm(forms.ModelForm):
#     class Meta:
#         model = SellerAccount
#         fields = ['bio', 'location']