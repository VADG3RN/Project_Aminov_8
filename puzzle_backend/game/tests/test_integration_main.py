import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User
from game.models import GameSession, Friendship, Challenge, Leaderboard
import json

@pytest.mark.django_db
class TestIntegrationMain:
    """Интеграционные тесты основного функционала игры"""
    
    def test_complete_game_scenario(self, api_client):
        """Полный сценарий: регистрация → игра → рекорд → лидерборд"""
        # 1. Регистрация
        register_url = reverse('register')
        user_data = {
            'username': 'fullscenariouser',
            'password': 'FullScenario123!',
            'email': 'full@example.com'
        }
        
        response = api_client.post(register_url, user_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # 2. Аутентификация
        auth_url = reverse('token-obtain')
        auth_data = {
            'username': 'fullscenariouser',
            'password': 'FullScenario123!'
        }
        
        response = api_client.post(auth_url, auth_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        token = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # 3. Начинаем новую игру
        session_url = reverse('gamesession-list')
        game_data = {
            'difficulty': 3,
            'game_state': {
                'tiles': [{'index': i} for i in range(9)],
                'emptyIndex': 8,
                'moves': 0,
                'timer': 0,
                'imageUrl': 'https://example.com/image.jpg'
            },
            'score': 0,
            'is_completed': False
        }
        
        response = api_client.post(session_url, game_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        session_id = response.data['id']
        
        # 4. Обновляем игру (имитируем игру)
        update_url = reverse('gamesession-detail', kwargs={'pk': session_id})
        update_data = {
            'game_state': {
                'tiles': [{'index': i} for i in range(9)],
                'emptyIndex': 8,
                'moves': 25,
                'timer': 180,
                'imageUrl': 'https://example.com/image.jpg'
            },
            'score': 8500,
            'is_completed': True
        }
        
        response = api_client.patch(update_url, update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # 5. Проверяем таблицу лидеров
        leaderboard_url = reverse('leaderboard')
        response = api_client.get(leaderboard_url)
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что наш результат есть в таблице лидеров
        leaderboard_data = response.data
        assert any(
            entry.get('user__username') == 'fullscenariouser' 
            for entry in leaderboard_data
        )
        
        # 6. Проверяем профиль
        profile_url = reverse('profile')
        response = api_client.get(profile_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'fullscenariouser'
        
        print("Полный сценарий игры выполнен успешно!")
        
    def test_friendship_and_challenge_scenario(self, api_client):
        """Сценарий: дружба → вызов → принятие вызова"""
        # Создаем двух пользователей
        user1_data = {
            'username': 'challengeuser1',
            'password': 'Challenge123!',
            'email': 'challenge1@example.com'
        }
        
        user2_data = {
            'username': 'challengeuser2',
            'password': 'Challenge123!',
            'email': 'challenge2@example.com'
        }
        
        # Регистрируем первого пользователя
        register_url = reverse('register')
        response = api_client.post(register_url, user1_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Аутентифицируем первого пользователя
        auth_url = reverse('token-obtain')
        auth_data = {
            'username': 'challengeuser1',
            'password': 'Challenge123!'
        }
        
        response = api_client.post(auth_url, auth_data, format='json')
        token1 = response.data['access']
        api_client.credentials(HTTP_ATPZUTHORIZATION=f'Bearer {token1}')
        
        # Добавляем второго пользователя в друзья
        friends_url = reverse('friends-list')
        friend_data = {'username': 'challengeuser2'}
        
        response = api_client.post(friends_url, friend_data, format='json')
        # Может быть 400 если пользователь не существует, поэтому сначала создадим его
        
        # Сбрасываем аутентификацию
        api_client.credentials()
        
        # Регистрируем второго пользователя
        response = api_client.post(register_url, user2_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Аутентифицируем первого пользователя снова
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        
        # Теперь добавляем в друзья
        response = api_client.post(friends_url, friend_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Отправляем вызов
        challenges_url = reverse('challenge-list')
        challenge_data = {
            'to_username': 'challengeuser2',
            'difficulty': 4,
            'target_score': 3000,
            'message': 'Прими мой вызов!'
        }
        
        response = api_client.post(challenges_url, challenge_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Сбрасываем аутентификацию и логинимся как второй пользователь
        api_client.credentials()
        
        auth_data = {
            'username': 'challengeuser2',
            'password': 'Challenge123!'
        }
        
        response = api_client.post(auth_url, auth_data, format='json')
        token2 = response.data['access']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        # Получаем входящие вызовы
        response = api_client.get(challenges_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0
        
        print("Сценарий дружбы и вызова выполнен успешно!")
        
    def test_data_integrity_after_operations(self):
        """Тест целостности данных после операций"""
        # Создаем пользователя
        user = User.objects.create_user(
            username='integrityuser',
            password='Integrity123!'
        )
        
        initial_session_count = GameSession.objects.filter(user=user).count()
        initial_leaderboard_score = Leaderboard.objects.get(user=user).best_score
        
        # Создаем несколько игровых сессий
        scores = [1000, 2000, 1500, 3000, 2500]
        
        for score in scores:
            GameSession.objects.create(
                user=user,
                difficulty=3,
                game_state={'tiles': []},
                score=score,
                is_completed=True
            )
        
        # Проверяем, что количество сессий увеличилось
        final_session_count = GameSession.objects.filter(user=user).count()
        assert final_session_count == initial_session_count + len(scores)
        
        # Проверяем, что в таблице лидеров лучший результат
        final_leaderboard_score = Leaderboard.objects.get(user=user).best_score
        assert final_leaderboard_score == max(scores)
        
        print("Целостность данных проверена успешно!")
        
    def test_concurrent_operations_simulation(self):
        """Тест симуляции конкурентных операций"""
        # Создаем несколько пользователей
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'concurrentuser{i}',
                password=f'Concurrent{i}!'
            )
            users.append(user)
        
        # Симулируем одновременное создание игровых сессий
        from game.models import GameSession
        
        sessions = []
        for user in users:
            session = GameSession.objects.create(
                user=user,
                difficulty=3,
                game_state={'tiles': []},
                score=1000,
                is_completed=True
            )
            sessions.append(session)
        
        # Проверяем, что все сессии созданы
        assert len(sessions) == len(users)
        
        # Проверяем таблицу лидеров для каждого пользователя
        for user in users:
            leaderboard = Leaderboard.objects.get(user=user)
            assert leaderboard.best_score == 1000
        
        print("Конкурентные операции симулированы успешно!")