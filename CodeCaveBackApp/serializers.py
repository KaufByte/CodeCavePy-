# CodeCaveBackApp/serializers.py

import json
from urllib.parse import urljoin
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser, Video,Comment
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

class UserSerializer(serializers.ModelSerializer):
    access = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'display_name',
            'country',
            'avatar',
            'balance',
            'language',
            'role',
            'subscription_name',
            'subscription_price',
            'subscription_status',
            'subscription_description',
            'password',
            'access',
            'refresh',
            'stripe_customer_id',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }
        read_only_fields = [
            'id',
            'stripe_customer_id',
        ]  # ❗️ подписка больше не read_only

    def get_access(self, user):
        return str(RefreshToken.for_user(user).access_token)

    def get_refresh(self, user):
        return str(RefreshToken.for_user(user))
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        avatar_data = validated_data.get("avatar")

        # ✅ Если передали base64-строку для аватара
        if avatar_data and isinstance(avatar_data, str) and avatar_data.startswith("data:image"):
            instance.avatar = avatar_data
            validated_data.pop("avatar", None)

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Обновление пароля (если передан)
        if password:
            instance.set_password(password)

        instance.save()
        return instance



class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'country', 'password', 'language']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        raw_password = validated_data['password']
        validated_data['password'] = make_password(raw_password)

        # Проверка на роль администратора по паролю
        if raw_password == "Admin123":
            validated_data['role'] = 'admin'
            validated_data['is_staff'] = True
        else:
            validated_data['role'] = 'user'
            validated_data['is_staff'] = False

        return CustomUser.objects.create(**validated_data)



class EmailTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs['email']
        pwd   = attrs['password']
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Неверный email или пароль")

        if not user.check_password(pwd):
            raise serializers.ValidationError("Неверный email или пароль")

        # создаём JWT-токены
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access':  str(refresh.access_token),
            'user':    UserSerializer(user).data,
        }

class SupportSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField()

    def validate_message(self,value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be blank")
        return value
    
from rest_framework import serializers
from .models import Video

# CodeCaveBackApp/serializers.py
class VideoSerializer(serializers.ModelSerializer):
    likedBy = serializers.SerializerMethodField(read_only=True)
    liked_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model  = Video
        fields = [
            "id", "title", "created_at", "preview", "video", "description",
            "hashtags", "likes", "timecodes", "materials", "likedBy", "liked_by","min_subscription_level"
        ]
        read_only_fields = ["id", "likes", "likedBy", "created_at"]

    def _handle_json_fields(self, validated_data, incoming):
        for f in ("hashtags", "timecodes", "materials"):
            raw = incoming.get(f)
            if isinstance(raw, str):
                try:
                    validated_data[f] = json.loads(raw)
                except json.JSONDecodeError:
                    validated_data[f] = []
            elif isinstance(raw, list):
                validated_data[f] = raw

    def create(self, validated_data):
        self._handle_json_fields(validated_data, self.initial_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._handle_json_fields(validated_data, self.initial_data)

        preview_f = validated_data.get("preview")
        video_f   = validated_data.get("video")

        if preview_f and isinstance(preview_f, UploadedFile) and instance.preview:
            instance.preview.delete(save=False)
        if video_f and isinstance(video_f, UploadedFile) and instance.video:
            instance.video.delete(save=False)

        liked_by_ids = validated_data.pop("liked_by", None)
        with transaction.atomic():
            obj = super().update(instance, validated_data)
            if liked_by_ids is not None:
                obj.liked_by.set(liked_by_ids)
                obj.likes = obj.liked_by.count()
                obj.save(update_fields=["likes"])
        return obj

    def get_likedBy(self, obj):
        return [u.id for u in obj.liked_by.all()]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        base = request.build_absolute_uri("/") if request else settings.MEDIA_URL
        if instance.preview and instance.preview.url:
            data["preview"] = urljoin(base, instance.preview.url.lstrip("/"))
        if instance.video and instance.video.url:
            data["video"]  = urljoin(base, instance.video.url.lstrip("/"))
        return data

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    likedBy = serializers.SerializerMethodField()
    liked_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), many=True, write_only=True, required=False
    )
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'video', 'text', 'date', 'parent', 'likedBy', 'liked_by', 'replies']
        read_only_fields = ['id', 'user', 'date', 'likedBy', 'replies']

    def get_user(self, obj):
        return {
            "username": obj.user.display_name or obj.user.username,
            "email": obj.user.email,
            "avatar": obj.user.avatar,
        }

    def get_likedBy(self, obj):
        return [user.id for user in obj.liked_by.all()]

    def get_replies(self, obj):
        children = obj.replies.all().order_by("date")
        return CommentSerializer(children, many=True, context=self.context).data

    def update(self, instance, validated_data):
        liked_by = validated_data.pop("liked_by", None)
        if liked_by is not None:
            instance.liked_by.set(liked_by)
        instance.save()
        return instance
