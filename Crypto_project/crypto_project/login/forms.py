from django import forms
from .models import CryptoCurrency, Purchase, Transaction, UserDetails

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput(), label='Confirm Password', required=True)

    class Meta:
        model = UserDetails
        fields = ['first_name', 'last_name', 'username', 'id_image', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match')


class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserDetails()
        fields  = ['username', 'first_name', 'last_name']

class AddMoneyForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount']

class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase
        fields = ['cryptocurrency', 'quantity']
        widgets = {
            'cryptocurrency': forms.Select(),
            'quantity': forms.TextInput(),
        }

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cryptocurrency'].queryset = CryptoCurrency.objects.all()
        self.user_id = user_id

    def clean(self):
        cleaned_data = super().clean()
        cryptocurrency = cleaned_data.get('cryptocurrency')
        quantity = cleaned_data.get('quantity')
        total_amount = cryptocurrency.current_price_cad * quantity
        cleaned_data['total_amount'] = total_amount
        return cleaned_data