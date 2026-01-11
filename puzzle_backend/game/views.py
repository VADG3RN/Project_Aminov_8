from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models import Max
from django.utils.dateparse import parse_date
from .models import GameSession, Friendship, UserProfile, Challenge, UserAchievement, Achievement
from .serializers import RegisterSerializer, ProfileSerializer, GameSessionSerializer, FriendSerializer, ChallengeSerializer, AchievementSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            # Обработка аватара (файл из FormData)
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
                profile.save()  # Сохраняем файл отдельно

            serializer.save()

            if 'email' in request.data:
                request.user.email = request.data.get('email', request.user.email)
                request.user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Публичный профиль для гостей
class PublicProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'username'

    def get_object(self):
        return UserProfile.objects.get(user__username=self.kwargs['username'])

class GameSessionViewSet(viewsets.ModelViewSet):
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GameSession.objects.filter(user=self.request.user, is_completed=False).order_by('-updated_at')

    def perform_create(self, serializer):
        # При новой игре завершаем предыдущую незавершённую
        previous = GameSession.objects.filter(user=self.request.user, is_completed=False).first()
        if previous:
            previous.is_completed = True
            previous.score = 0  # Или рассчитай текущий, если нужно
            previous.save()

        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

class LeaderboardView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        difficulty = request.query_params.get('difficulty')
        friends = request.query_params.get('friends') == 'true'
        date_from = parse_date(request.query_params.get('date_from', ''))
        date_to = parse_date(request.query_params.get('date_to', ''))

        queryset = GameSession.objects.filter(is_completed=True)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if date_from:
            queryset = queryset.filter(updated_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(updated_at__date__lte=date_to)

        if friends and request.user.is_authenticated:
            friend_ids = Friendship.objects.filter(from_user=request.user).values_list('to_user_id', flat=True)
            queryset = queryset.filter(user__in=friend_ids)

        results = queryset.values('user__username').annotate(best_score=Max('score')).order_by('-best_score')

        for rank, entry in enumerate(results, start=1):
            entry['rank'] = rank

        return Response(list(results)[:50])

# Список достижений пользователя
class UserAchievementListView(generics.ListAPIView):
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Achievement.objects.filter(userachievement__user=self.request.user)

class FriendListCreateView(generics.ListCreateAPIView):
    serializer_class = FriendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Friendship.objects.filter(from_user=self.request.user)

    def perform_create(self, serializer):
        username = self.request.data.get('username')
        
        if not username:
            raise ValidationError({"username": "Укажите имя пользователя для добавления."})
        
        if username.lower() == self.request.user.username.lower():
            raise ValidationError({"username": "Нельзя добавить самого себя в друзья! 😅"})
        
        try:
            to_user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise ValidationError({"username": "Пользователь с таким именем не существует."})
        
        if Friendship.objects.filter(from_user=self.request.user, to_user=to_user).exists():
            raise ValidationError({"username": "Этот пользователь уже в ваших друзьях."})
        
        serializer.save(from_user=self.request.user, to_user=to_user)

class FriendDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Friendship.objects.filter(from_user=self.request.user)

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Challenge.objects.filter(to_user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        to_username = self.request.data.get('to_username')
        
        if not to_username:
            raise ValidationError({"to_username": "Укажите имя пользователя для вызова."})
        
        if to_username.lower() == self.request.user.username.lower():
            raise ValidationError({"to_username": "Нельзя отправить вызов самому себе! 😅"})
        
        try:
            to_user = User.objects.get(username__iexact=to_username)
        except User.DoesNotExist:
            raise ValidationError({"to_username": "Пользователь с таким именем не существует."})
        
        if not Friendship.objects.filter(from_user=self.request.user, to_user=to_user).exists():
            raise ValidationError({"to_username": "Вызов можно отправлять только друзьям."})
        
        serializer.save(
            difficulty=self.request.data.get('difficulty'),
            target_score=self.request.data.get('target_score')
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.to_user != request.user:
            raise ValidationError("Можно редактировать только свои полученные вызовы.")
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)