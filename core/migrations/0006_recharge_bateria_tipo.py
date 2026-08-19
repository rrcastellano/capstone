from django.db import migrations, models

def add_columns(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE core_recharge ADD COLUMN IF NOT EXISTS bateria_antes integer;
            ALTER TABLE core_recharge ADD COLUMN IF NOT EXISTS bateria_depois integer;
            ALTER TABLE core_recharge ADD COLUMN IF NOT EXISTS tipo_recarga varchar(10);
        """)
    elif schema_editor.connection.vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(core_recharge)")
            cols = [row[1] for row in cursor.fetchall()]
        if 'bateria_antes' not in cols:
            schema_editor.execute("ALTER TABLE core_recharge ADD COLUMN bateria_antes integer;")
        if 'bateria_depois' not in cols:
            schema_editor.execute("ALTER TABLE core_recharge ADD COLUMN bateria_depois integer;")
        if 'tipo_recarga' not in cols:
            schema_editor.execute("ALTER TABLE core_recharge ADD COLUMN tipo_recarga varchar(10);")

def reverse_columns(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE core_recharge DROP COLUMN IF EXISTS bateria_antes;
            ALTER TABLE core_recharge DROP COLUMN IF EXISTS bateria_depois;
            ALTER TABLE core_recharge DROP COLUMN IF EXISTS tipo_recarga;
        """)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_recharge_latitude_longitude'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_columns, reverse_columns)
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
