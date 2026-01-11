import os
import sys
import django
import pytest
import tempfile
from PIL import Image

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'puzzle_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Инициализируем Django
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from game.models import (
    UserProfile, Achievement, UserAchievement, GameSession,
    Friendship, Leaderboard, Challenge
)

# Тестовые фикстуры
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def client():
    """Django тестовый клиент (вместо django_client)"""
    return Client()

@pytest.fixture
def django_client(client):
    """Алиас для client для обратной совместимости"""
    return client

@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return User.objects.create_user(**kwargs)
    return make_user

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )

@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        username='anotheruser',
        password='anotherpass123',
        email='another@example.com'
    )

@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin',
        password='adminpass123',
        email='admin@example.com'
    )

@pytest.fixture
def authenticated_client(api_client, user):
    """Аутентифицированный APIClient"""
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    """Аутентифицированный APIClient для админа"""
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def user_profile(user):
    """Профиль пользователя"""
    return UserProfile.objects.get(user=user)

@pytest.fixture
def test_achievement(db):
    """Тестовое достижение"""
    return Achievement.objects.create(
        name='Test Achievement',
        description='Test Description'
    )

@pytest.fixture
def test_game_session(user, db):
    """Тестовая игровая сессия"""
    return GameSession.objects.create(
        user=user,
        difficulty=3,
        game_state={'tiles': [{'index': 0}, {'index': 1}, {'index': 2}]},
        score=1000,
        is_completed=True
    )

@pytest.fixture
def test_friendship(user, another_user, db):
    """Тестовая дружба"""
    return Friendship.objects.create(
        from_user=user,
        to_user=another_user
    )

@pytest.fixture
def test_image():
    """Тестовое изображение"""
    image = Image.new('RGB', (100, 100), color='red')
    tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    image.save(tmp_file, 'JPEG')
    tmp_file.seek(0)
    return SimpleUploadedFile(
        name='test_image.jpg',
        content=tmp_file.read(),
        content_type='image/jpeg'
    )

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Включаем доступ к базе данных для всех тестов"""
    pass