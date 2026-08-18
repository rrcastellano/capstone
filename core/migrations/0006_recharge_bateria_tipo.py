from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_recharge_latitude_longitude'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE core_recharge ADD COLUMN IF NOT EXISTS bateria_antes integer;
                    ALTER TABLE core_recharge ADD COLUMN IF NOT EXISTS bateria_depois integer;
                    ALTER TABLE core_recharge ADD COLUMN IF NOT EXISTS tipo_recarga varchar(10);
                    """,
                    reverse_sql="""
                    ALTER TABLE core_recharge DROP COLUMN IF EXISTS bateria_antes;
                    ALTER TABLE core_recharge DROP COLUMN IF EXISTS bateria_depois;
                    ALTER TABLE core_recharge DROP COLUMN IF EXISTS tipo_recarga;
                    """
                )
            ],
            state_operations=[
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
            ]
        )
    ]
