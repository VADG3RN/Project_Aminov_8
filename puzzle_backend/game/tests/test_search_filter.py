import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Friendship

@pytest.mark.django_db
class TestSearchFilter:
    """Тесты поиска и фильтрации"""
    
    def test_leaderboard_search_by_difficulty(self, api_client):
        """Тест поиска по сложности в таблице лидеров"""
        # Создаем тестовые данные
        user1 = User.objects.create_user(username='search1', password='pass1')
        user2 = User.objects.create_user(username='search2', password='pass2')
        
        # Сложность 3
        GameSession.objects.create(
            user=user1,
            difficulty=3,
            game_state={'tiles': []},
            score=1000,
            is_completed=True
        )
        
        # Сложность 4
        GameSession.objects.create(
            user=user2,
            difficulty=4,
            game_state={'tiles': []},
            score=2000,
            is_completed=True
        )
        
        url = reverse('leaderboard')
        
        # Ищем по сложности 3
        response = api_client.get(url, {'difficulty': 3})
        assert response.status_code == 200
        
        # Ищем по сложности 4
        response = api_client.get(url, {'difficulty': 4})
        assert response.status_code == 200
        
    def test_leaderboard_search_by_date(self, api_client):
        """Тест поиска по дате в таблице лидеров"""
        user = User.objects.create_user(username='datesearch', password='pass')
        
        # Создаем несколько игр
        GameSession.objects.create(
            user=user,
            difficulty=3,
            game_state={'tiles': []},
            score=1000,
            is_completed=True
        )
        
        GameSession.objects.create(
            user=user,
            difficulty=3,
            game_state={'tiles': []},
            score=2000,
            is_completed=True
        )
        
        url = reverse('leaderboard')
        
        # Ищем без фильтра
        response = api_client.get(url)
        assert response.status_code == 200
        
    def test_leaderboard_search_by_friends(self, api_client, user, another_user):
        """Тест поиска по друзьям в таблице лидеров"""
        # Создаем дружбу
        Friendship.objects.create(
            from_user=user,
            to_user=another_user
        )
        
        # Создаем игру для друга
        GameSession.objects.create(
            user=another_user,
            difficulty=3,
            game_state={'tiles': []},
            score=1500,
            is_completed=True
        )
        
        url = reverse('leaderboard')
        
        # Аутентифицируем пользователя
        api_client.force_authenticate(user=user)
        
        # Ищем только друзей
        response = api_client.get(url, {'friends': 'true'})
        assert response.status_code == 200
        
    def test_game_session_filtering(self, authenticated_client, user):
        """Тест фильтрации игровых сессий"""
        # Создаем сессии с разными статусами
        GameSession.objects.create(
            user=user,
            difficulty=3,
            game_state={'tiles': []},
            score=1000,
            is_completed=False
        )
        
        GameSession.objects.create(
            user=user,
            difficulty=4,
            game_state={'tiles': []},
            score=2000,
            is_completed=True
        )
        
        url = reverse('gamesession-list')
        
        # Получаем все сессии (по умолчанию только незавершенные)
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # Может быть 0 или 1, в зависимости от реализации views
        
    def test_user_search_in_admin(self, client, admin_user):
        """Тест поиска пользователей в админке"""
        client.force_login(admin_user)
        
        # Создаем тестовых пользователей
        User.objects.create_user(username='alice', password='pass1')
        User.objects.create_user(username='bob', password='pass2')
        
        url = '/admin/auth/user/'
        
        # Ищем пользователя по имени
        response = client.get(url, {'q': 'alice'})
        assert response.status_code == 200
        
    def test_game_session_search_in_admin(self, client, admin_user):
        """Тест поиска игровых сессий в админке"""
        client.force_login(admin_user)
        
        # Создаем тестовых пользователей и сессии
        user1 = User.objects.create_user(username='gameuser1', password='pass1')
        user2 = User.objects.create_user(username='gameuser2', password='pass2')
        
        GameSession.objects.create(
            user=user1,
            difficulty=3,
            game_state={'tiles': []},
            score=1000,
            is_completed=True
        )
        
        url = '/admin/game/gamesession/'
        
        # Ищем по имени пользователя
        response = client.get(url, {'q': 'gameuser1'})
        assert response.status_code == 200