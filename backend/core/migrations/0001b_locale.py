from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Locale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(blank=True, default='', max_length=64)),
            ],
            options={
                'app_label': 'core',
            },
        ),
    ]
