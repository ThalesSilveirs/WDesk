from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0027_pendency_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.TextField(blank=True, null=True),
        ),
    ]
