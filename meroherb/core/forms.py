from django import forms

from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User

class LoginForm(AuthenticationForm):
    username=forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Your username',
        'class':'usernamebox',

    }))
    password=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Password',
        'class':'passwordbox',

    }))

class SignupForm(UserCreationForm):
    class Meta:
        model=User
        fields=('username','email','password1','password2','first_name','last_name','contact_number')

    username=forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':'Your username',
        'class':'usernamebox'
    }))
    email=forms.CharField(widget=forms.EmailInput(attrs={
        'placeholder':'Your email',
        'class':'emailbox'

    }))
    password1=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Password',
        'class':'passwordbox'

    }))
    password2=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Retype Password',
        'class':'passwordbox'


    }))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Your first name',
        'class':'firstnamebox'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'placeholder': 'Your last name',
        'class':'lastnamebox'
    }))
    contact_number = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'placeholder': 'Your contact number',
        'class':'contactbox'
    }))
    location = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'placeholder': 'Your location',
        'class':'locationbox'
    }))

