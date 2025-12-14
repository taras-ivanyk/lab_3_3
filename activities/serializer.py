# activities/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Activity,
    Profile,
    Comment,
    Kudos,
    Follower,
    ActivityPoint,
    UserMonthlyStats
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''), # .get() is safer
            password=validated_data['password']
        )
        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('user',)


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ('user',)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('user',)

class KudosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kudos
        fields = '__all__'
        read_only_fields = ('user',)

class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = '__all__'
        read_only_fields = ('follower',)

class ActivityPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityPoint
        fields = '__all__'

class UserMonthlyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMonthlyStats
        fields = '__all__'
        read_only_fields = ('user',)