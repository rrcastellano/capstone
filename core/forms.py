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
    data = forms.DateTimeField(
        label=_('Data'),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
    )

    class Meta:
        model = Recharge
        fields = [
            'data', 'odometro', 'kwh', 'custo', 'isento',
            'tipo_recarga', 'bateria_antes', 'bateria_depois',
            'local', 'latitude', 'longitude', 'observacoes'
        ]
        labels = {
            'data': _('Data'),
            'odometro': _('Odômetro'),
            'kwh': _('kWh'),
            'custo': _('Custo'),
            'isento': _('Isento'),
            'tipo_recarga': _('Tipo de Recarga (AC/DC)'),
            'bateria_antes': _('Bateria Antes (%)'),
            'bateria_depois': _('Bateria Depois (%)'),
            'local': _('Local'),
            'latitude': _('Latitude'),
            'longitude': _('Longitude'),
            'observacoes': _('Observações'),
        }
        widgets = {
            'odometro': forms.NumberInput(attrs={'class': 'form-control'}),
            'kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'isento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tipo_recarga': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AC / DC'}),
            'bateria_antes': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '%'}),
            'bateria_depois': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '%'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': _('Opcional...')}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': _('Opcional...')}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('Opcional...')}),
        }
