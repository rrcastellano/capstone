from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_secure_rls'),
    ]

    operations = [
        migrations.AddField(
            model_name='recharge',
            name='bateria_antes',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recharge',
            name='bateria_depois',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recharge',
            name='tipo_recarga',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='recharge',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recharge',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
