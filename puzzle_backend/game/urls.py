from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, ProfileView, PublicProfileView, LeaderboardView,
    GameSessionViewSet, FriendListCreateView, FriendDeleteView,
    ChallengeViewSet, UserAchievementListView
)

router = DefaultRouter()
router.register(r'sessions', GameSessionViewSet)
router.register(r'challenges', ChallengeViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),  # Свой профиль
    path('profile/<str:username>/', PublicProfileView.as_view(), name='public-profile'), 
    path('achievements/', UserAchievementListView.as_view(), name='achievements'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('friends/', FriendListCreateView.as_view(), name='friends-list'),
    path('friends/<int:pk>/', FriendDeleteView.as_view(), name='friend-delete'),
    path('token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('', include(router.urls)),
]