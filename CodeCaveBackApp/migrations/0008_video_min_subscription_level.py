# Generated by Django 5.1.7 on 2025-05-14 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CodeCaveBackApp', '0007_customuser_stripe_customer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='min_subscription_level',
            field=models.CharField(choices=[('Free', 'Free'), ('Junior', 'Junior'), ('Chilli Middle', 'Chilli Middle'), ('Powerful SEO', 'Powerful SEO')], default='Free', max_length=50),
        ),
    ]
