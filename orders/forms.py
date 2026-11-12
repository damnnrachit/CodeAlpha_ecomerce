from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    """
    Form capturing customer shipping destination details.
    """
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe',
            'autocomplete': 'name',
        })
    )
    address = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123 Main St, Apt 4B',
            'autocomplete': 'street-address',
        })
    )
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'New York',
            'autocomplete': 'address-level2',
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10001',
            'autocomplete': 'postal-code',
        })
    )

    class Meta:
        model = Order
        fields = ('full_name', 'address', 'city', 'postal_code')
