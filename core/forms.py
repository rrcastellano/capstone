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

TIPO_RECARGA_CHOICES = [
    ('AC', 'AC'),
    ('DC', 'DC'),
]

class RechargeForm(forms.ModelForm):
    data = forms.DateTimeField(
        label=_('Data'),
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        ),
        input_formats=[
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            'iso-8601'
        ]
    )
    tipo_recarga = forms.ChoiceField(
        choices=TIPO_RECARGA_CHOICES,
        initial='AC',
        required=True,
        label=_('Tipo de Recarga'),
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    bateria_antes = forms.IntegerField(
        required=False,
        label=_('Bateria Antes (%)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '%'})
    )
    bateria_depois = forms.IntegerField(
        required=False,
        label=_('Bateria Depois (%)'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': '%'})
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
            'tipo_recarga': _('Tipo de Recarga'),
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
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': _('Opcional...')}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': _('Opcional...')}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('Opcional...')}),
        }

    def clean_data(self):
        data_val = self.cleaned_data.get('data')
        if not data_val:
            return data_val

        from django.utils import timezone
        import datetime

        if isinstance(data_val, str):
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(data_val)
            if parsed:
                data_val = parsed
            else:
                try:
                    data_val = datetime.datetime.fromisoformat(data_val.replace('Z', '+00:00'))
                except Exception:
                    pass

        if isinstance(data_val, datetime.datetime):
            if timezone.is_naive(data_val):
                data_val = timezone.make_aware(data_val, timezone.get_current_timezone())
            return data_val.astimezone(datetime.timezone.utc)

        return data_val

    def clean(self):
        cleaned_data = super().clean()
        antes = cleaned_data.get('bateria_antes')
        depois = cleaned_data.get('bateria_depois')

        # 1. Salvar com bateria vazia
        if antes is None or depois is None:
            msg = _("Informe o percentual da bateria antes e depois da recarga.")
            if antes is None:
                self.add_error('bateria_antes', msg)
            if depois is None:
                self.add_error('bateria_depois', msg)
            raise forms.ValidationError(msg)

        # 2. Fora de 0-100
        if antes < 0 or antes > 100 or depois < 0 or depois > 100:
            msg = _("A bateria deve estar entre 0 e 100 %.")
            if antes < 0 or antes > 100:
                self.add_error('bateria_antes', msg)
            if depois < 0 or depois > 100:
                self.add_error('bateria_depois', msg)
            raise forms.ValidationError(msg)

        # 3. Depois menor que antes
        if depois < antes:
            msg = _("A bateria depois não pode ser menor que antes da recarga.")
            self.add_error('bateria_depois', msg)
            raise forms.ValidationError(msg)

        return cleaned_data
