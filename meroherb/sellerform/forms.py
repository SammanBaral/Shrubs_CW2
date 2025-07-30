from django import forms
from .models import SellerAccount

class UserProfilePhotoForm(forms.ModelForm):
    class Meta:
        model=SellerAccount
        fields=('image',)

        widgets={
            'image': forms.FileInput(attrs={
                'class': 'image_input',
                'name':'image',  # name should match the widget name of input field
            }),
        }