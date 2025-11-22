from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'avatar_url', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_staff", "profile")
        read_only_fields = ("id", "is_staff")

