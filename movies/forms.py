# forms.py
from django import forms

class RegisterForm(forms.Form):
    user_id = forms.IntegerField(label="ID Utilisateur")
    password = forms.CharField(widget=forms.PasswordInput)

class LoginForm(forms.Form):
    user_id = forms.IntegerField(label="ID Utilisateur")
    password = forms.CharField(widget=forms.PasswordInput)