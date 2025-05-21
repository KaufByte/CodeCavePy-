from datetime import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # теперь username — обязательное дополнительное

    email = models.EmailField(unique=True)
    avatar = models.TextField(blank=True, null=True)
    display_name = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    role = models.CharField(max_length=20, default="user")
    language = models.CharField(max_length=10, default="en")

    stripe_customer_id = models.CharField(max_length=100,blank=True,null=True)
    
    subscription_name = models.CharField(max_length=100, default="Free")
    subscription_price = models.CharField(max_length=50, default="0.00")
    subscription_status = models.CharField(max_length=50, default="Inactive")
    subscription_description = models.TextField(blank=True, default="")


    # Переопределяем связи на группы
    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="customuser_groups",      # вот здесь изменили
        related_query_name="customuser",
    )

    # Переопределяем связи на права
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="customuser_permissions",  # и здесь
        related_query_name="customuser",
    )

    def __str__(self):
        return self.username
class SupportMessage(models.Model):
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Video(models.Model):
    title = models.CharField(max_length=255)
    date_ua = models.CharField(max_length=50)
    date_us = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    preview = models.ImageField(upload_to="images/")
    video = models.FileField(upload_to="videos/")
    description = models.TextField()
    hashtags = models.JSONField(default=list)
    likes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(CustomUser, blank=True, related_name='liked_videos')
    timecodes = models.JSONField(default=list)
    materials = models.JSONField(default=list)

    min_subscription_level = models.CharField(
        max_length=50,
        choices=[
            ("Free", "Free"),
            ("Junior", "Junior"),
            ("Chilli Middle", "Chilli Middle"),
            ("Powerful SEO", "Powerful SEO"),
        ],
        default="Free"
    )
    def __str__(self):
        return self.title

class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    liked_by = models.ManyToManyField(CustomUser, blank=True, related_name='liked_comments')

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"