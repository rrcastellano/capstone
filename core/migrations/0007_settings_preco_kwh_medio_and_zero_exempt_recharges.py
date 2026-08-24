from django.db import migrations, models

def apply_migration(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE core_settings 
            ADD COLUMN IF NOT EXISTS preco_kwh_medio NUMERIC DEFAULT 2.60;

            UPDATE core_recharge 
            SET custo = 0 
            WHERE isento = true AND custo != 0;
        """)
    elif schema_editor.connection.vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(core_settings)")
            cols = [row[1] for row in cursor.fetchall()]
        if 'preco_kwh_medio' not in cols:
            schema_editor.execute("ALTER TABLE core_settings ADD COLUMN preco_kwh_medio real DEFAULT 2.60;")
        schema_editor.execute("UPDATE core_recharge SET custo = 0 WHERE isento = 1 AND custo != 0;")

def reverse_migration(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE core_settings DROP COLUMN IF EXISTS preco_kwh_medio;
        """)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_recharge_bateria_tipo'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(apply_migration, reverse_migration)
            ],
            state_operations=[
                migrations.AddField(
                    model_name='settings',
                    name='preco_kwh_medio',
                    field=models.FloatField(default=2.6),
                ),
            ]
        )
    ]
