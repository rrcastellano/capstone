from django import forms
from .models import ContactLog, Recharge, Settings
from django.contrib.auth.models import User

from django.utils.translation import gettext_lazy as _

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactLog
        fields = ['nome', 'email', 'mensagem']
        labels = {
            'nome': _('Nome'),
            'email': _('Email'),
            'mensagem': _('Mensagem'),
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Seu nome')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Seu e-mail')}),
            'mensagem': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Sua mensagem'), 'rows': 4}),
        }

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ['preco_gasolina', 'consumo_km_l']
        labels = {
            'preco_gasolina': _('Preço da Gasolina (R$)'),
            'consumo_km_l': _('Consumo Gasolina (Km/l)'),
        }
        widgets = {
            'preco_gasolina': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'consumo_km_l': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    nome = forms.CharField(label=_("Nome (Primeiro Nome)"), required=True)
    email = forms.EmailField(label=_("Email"), required=True)
    
    class Meta:
        model = User
        fields = ("username", "email", "nome")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["nome"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class RechargeForm(forms.ModelForm):
    class Meta:
        model = Recharge
        fields = ['data', 'odometro', 'kwh', 'custo', 'isento', 'observacoes', 'local']
        labels = {
            'data': _('Data'),
            'odometro': _('Odômetro'),
            'kwh': _('kWh'),
            'custo': _('Custo'),
            'isento': _('Isento'),
            'observacoes': _('Observações'),
            'local': _('Local'),
        }
        widgets = {
            'data': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'odometro': forms.NumberInput(attrs={'class': 'form-control'}),
            'kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'isento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('Opcional...')}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
        }
