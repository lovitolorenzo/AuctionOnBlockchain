from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import *



class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2','user_permissions','is_staff']

class Product(UserCreationForm):
    class Meta:
        model = Product
        fields = ['name','digital','start_date','base_price','end_date', 'bidding_finished', 'image']

class CreateClosedForm(forms.ModelForm):
    class Meta:
        model = ClosedAuction
        fields = []

