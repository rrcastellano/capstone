from django.db import models
from django.contrib.auth.models import User

class Recharge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.DateTimeField()
    kwh = models.FloatField()
    custo = models.FloatField()
    isento = models.BooleanField(default=False)
    odometro = models.FloatField()
    observacoes = models.TextField(blank=True, null=True)
    TIPO_RECARGA_CHOICES = [
        ('AC', 'AC'),
        ('DC', 'DC'),
    ]

    local = models.CharField(max_length=100, blank=True, null=True)
    bateria_antes = models.IntegerField(blank=True, null=True)
    bateria_depois = models.IntegerField(blank=True, null=True)
    tipo_recarga = models.CharField(max_length=10, choices=TIPO_RECARGA_CHOICES, default='AC')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.isento:
            self.custo = 0.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.data}"

class Settings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preco_gasolina = models.FloatField()
    consumo_km_l = models.FloatField()
    preco_kwh_medio = models.FloatField(default=2.60)

    def __str__(self):
        return f"Settings for {self.user.username}"

class ContactLog(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(max_length=255)
    mensagem = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.email} - {self.status}"
