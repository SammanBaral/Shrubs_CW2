from django import forms
from .models import Bill, Item


class NewItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('category', 'name','scientific_name', 'description', 'usage_and_benefits', 'price', 'quantity_available', 'image', )

        widgets = {
            'category': forms.Select(attrs={
                'class': 'category_input'
                
            }),

            'name': forms.TextInput(attrs={
                'class': 'name_input',  # Apply the text-input class from your CSS
                'placeholder':'Name'
            }),

            'scientific_name': forms.TextInput(attrs={
                'class': 'name_input',  # Apply the text-input class from your CSS
                'placeholder':'Scientific name'

            }),

            'description': forms.Textarea(attrs={
                'class': 'description_input',  # Apply the text-input-description class from your CSS
                'placeholder':'Description'

            }),

            'usage_and_benefits': forms.Textarea(attrs={
                'class': 'usage_input',  # Apply the text-input-usage-benefit class from your CSS
                'placeholder':'Usage and benefits'

            }),

            'price': forms.TextInput(attrs={
                'class': 'price_input',  # Apply the text-input-price-field class from your CSS
                'placeholder':'Price'

            }),

            'quantity_available': forms.TextInput(attrs={
                'class': 'quantity_input'  # Apply the text-input-quantity-field class from your CSS
            }),

         
        }

class EditItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('name','scientific_name', 'description', 'usage_and_benefits', 'price', 'quantity_available', 'image','discount', )

        widgets = {

            'name': forms.TextInput(attrs={
                'class': 'name_input',  # Apply the text-input class from your CSS
                'placeholder':'Name'
            }),

            'scientific_name': forms.TextInput(attrs={
                'class': 'name_input',  # Apply the text-input class from your CSS
                'placeholder':'Scientific name'

            }),

            'description': forms.Textarea(attrs={
                'class': 'description_input',  # Apply the text-input-description class from your CSS
                'placeholder':'Description'

            }),

            'usage_and_benefits': forms.Textarea(attrs={
                'class': 'usage_input',  # Apply the text-input-usage-benefit class from your CSS
                'placeholder':'Usage and benefits'

            }),

            'price': forms.TextInput(attrs={
                'class': 'price_input',  # Apply the text-input-price-field class from your CSS
                'placeholder':'Price'

            }),

            'quantity_available': forms.TextInput(attrs={
                'class': 'quantity_input', # Apply the text-input-quantity-field class from your CSS
                'placeholder':'Quantity in gms'
            }),

            'image': forms.FileInput(attrs={
                'class': 'image_input'
            }),
            'discount': forms.TextInput(attrs={
                'class': 'discount_input',  # Apply the text-input-price-field class from your CSS
                'placeholder':'Discount'

            }),
        }

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['customer', 'item', 'quantity', 'total_amount']




