from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, GameSession, Friendship, Challenge, Achievement, UserAchievement

class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        UserProfile.objects.get_or_create(user=user) 
        return user

class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля (с username/email из User)."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)  

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'avatar', 'bio', 'date_of_birth')
        read_only_fields = ('username', 'email')

class GameSessionSerializer(serializers.ModelSerializer):
    """Сериализатор игровых сессий."""
    class Meta:
        model = GameSession
        fields = '__all__'
        read_only_fields = ('user', 'time_played')  # time_played рассчитывается автоматически

class FriendSerializer(serializers.ModelSerializer):
    """Сериализатор для списка друзей."""
    username = serializers.CharField(source='to_user.username', read_only=True)
    # Опционально: avatar = serializers.ImageField(source='to_user.profile.avatar', read_only=True)

    class Meta:
        model = Friendship
        fields = ('id', 'username', 'created_at')
        read_only_fields = fields

class AchievementSerializer(serializers.ModelSerializer):
    """Сериализатор достижений."""
    class Meta:
        model = Achievement
        fields = ('id', 'name', 'description', 'icon')

class UserAchievementSerializer(serializers.ModelSerializer):
    """Сериализатор для списка достижений пользователя."""
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ('achievement', 'created_at')

class ChallengeSerializer(serializers.ModelSerializer):
    """Сериализатор вызовов."""
    from_username = serializers.CharField(source='from_user.username', read_only=True)
    to_username = serializers.CharField(write_only=True)

    class Meta:
        model = Challenge
        fields = [
            'id', 'from_username', 'to_username', 'difficulty', 'target_score',
            'message', 'is_accepted', 'is_completed', 'response_score', 'created_at'
        ]
        read_only_fields = ['id', 'from_username', 'created_at']

    def create(self, validated_data):
        to_username = validated_data.pop('to_username')
        try:
            to_user = User.objects.get(username=to_username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"to_username": "Пользователь не найден."})
        return Challenge.objects.create(
            from_user=self.context['request'].user,
            to_user=to_user,
            **validated_data
        )