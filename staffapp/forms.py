# forms.py
from django import forms

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Enter your email", max_length=254)


