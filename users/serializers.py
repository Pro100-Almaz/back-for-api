from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from .models import UserProfile, Avatar
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
import boto3

from .models import Avatar
from .validators import validate_user_avatar_key

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['website', 'location', 'skills', 'email_notifications', 'marketing_emails']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'role',
            'phone_number', 'company_name', 'bio', 'points_balance',
            'api_key', 'total_revenue', 'total_payouts', 'profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'role', 'points_balance', 'api_key', 'total_revenue',
            'total_payouts', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = User.objects.create_user(**validated_data)

        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)

        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile if provided
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'password',
            'password_confirm', 'phone_number', 'company_name', 'bio',
            'profile'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profile_data = validated_data.pop('profile', None)

        # Create user with default role (CLIENT)
        user = User.objects.create_user(**validated_data)

        # Create profile
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)

        return user


class ClientRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for client registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'password',
            'password_confirm', 'phone_number', 'company_name', 'bio',
            'profile'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profile_data = validated_data.pop('profile', None)

        # Create user with CLIENT role
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.CLIENT
        )

        # Create profile
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)

        return user


class ToolCreatorRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for tool creator registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'password',
            'password_confirm', 'phone_number', 'company_name', 'bio',
            'profile'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profile_data = validated_data.pop('profile', None)

        # Create user with TOOL_CREATOR role
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.TOOL_CREATOR
        )

        # Create profile
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)

        return user


class AdminRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for admin registration (admin only)"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'password',
            'password_confirm', 'phone_number', 'company_name', 'bio',
            'profile'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profile_data = validated_data.pop('profile', None)

        # Create user with ADMIN role
        user = User.objects.create_user(
            **validated_data,
            role=User.Role.ADMIN
        )

        # Create profile
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)

        return user


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users with basic info"""

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role', 'created_at']


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin operations on users"""
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'role',
            'phone_number', 'company_name', 'bio', 'avatar', 'points_balance',
            'api_key', 'total_revenue', 'total_payouts', 'profile',
            'is_active', 'is_staff', 'is_superuser', 'created_at', 'updated_at'
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile if provided
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class ToolCreatorSerializer(serializers.ModelSerializer):
    """Serializer for tool creator specific operations"""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'api_key', 'total_revenue', 'total_payouts', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for client specific operations"""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'points_balance', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AvatarCreateSerializer(serializers.Serializer):
    path = serializers.CharField(write_only=True)         # desired key
    avatar = serializers.ImageField(write_only=True)      # file bytes

    key = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)

    def validate(self, attrs):
        user = self.context["request"].user

        # path/key checks (ownership, no '..', has filename, allowed chars/ext, etc.)
        try:
            attrs["key"] = validate_user_avatar_key(user.id, attrs["path"])
        except ValueError as e:
            raise serializers.ValidationError({"path": str(e)})

        f = attrs["avatar"]
        if getattr(f, "size", 0) > 5 * 1024 * 1024:
            raise serializers.ValidationError({"avatar": "Max size is 5 MB"})
        if not str(getattr(f, "content_type", "")).startswith("image/"):
            raise serializers.ValidationError({"avatar": "Only image/* content types are allowed"})
        return attrs

    def create(self, validated):
        user = self.context["request"].user
        key  = validated["key"]
        file = validated["avatar"]

        # optional overwrite flag
        allow_overwrite = self.context["request"].query_params.get("overwrite") in {"1", "true", "True"}

        # for OneToOne: update existing or create new
        av, _created = Avatar.objects.get_or_create(user=user)

        # if an object already exists at this key and overwrite not allowed → 400
        if default_storage.exists(key) and not allow_overwrite:
            raise serializers.ValidationError({"path": "Object already exists at this key. Use ?overwrite=true to replace."})
        if allow_overwrite and default_storage.exists(key):
            default_storage.delete(key)

        # Save through the ImageField so DB + storage stay in sync
        # name=<key> forces the exact storage path you validated
        av.key = key
        av.avatar.save(name=key, content=file, save=True)  # writes to storage & updates field name

        # Build URL (S3: signed if AWS_QUERYSTRING_AUTH=True)
        url = av.avatar.url

        return {"key": av.avatar.name, "url": url}

class AvatarDetailSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Avatar
        fields = ("id", "key", "url", "created_at")

    def get_url(self, obj):
        # use storage.url if signed (AWS_QUERYSTRING_AUTH=True), else boto3 presign
        try:
            return default_storage.url(obj.key)
        except Exception:
            return presign_get(obj.key)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        token['is_admin'] = user.is_admin
        token['is_tool_creator'] = user.is_tool_creator
        token['is_client'] = user.is_client
        token['email'] = user.email
        token['username'] = user.username
        return token
