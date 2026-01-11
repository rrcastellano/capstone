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
    local = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.data}"

class Settings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preco_gasolina = models.FloatField()
    consumo_km_l = models.FloatField()

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
