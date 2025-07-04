from django import forms
from django.contrib.auth.models import User
from .models import UserInfo

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ['phone_number', 'address', 'pancard_number', 'user_image', 'pancard_image']

class BuyStockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity")


class SellStockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity")
