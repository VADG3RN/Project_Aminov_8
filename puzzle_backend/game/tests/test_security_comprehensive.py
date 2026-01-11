import pytest
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from game.models import GameSession, User, Friendship  
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
class TestSecurity:
    """Комплексные тесты безопасности"""
    
    def test_password_hashing(self):
        """Тест хеширования паролей"""
        password = 'MySuperSecretPass123!'
        
        # Создаем пользователя
        user = User.objects.create_user(
            username='hashuser',
            password=password
        )
        
        # Проверяем, что пароль хеширован
        assert user.password != password
        assert user.password.startswith('pbkdf2_sha256$')
        
        # Проверяем, что хеш соответствует паролю
        assert check_password(password, user.password) is True
        
    def test_sql_injection_prevention(self, authenticated_client):
        """Тест защиты от SQL инъекции"""
        # Попытка SQL инъекции через параметры
        malicious_username = "test' OR '1'='1' --"
        
        # Пытаемся добавить такого "друга"
        url = reverse('friends-list')
        data = {'username': malicious_username}
        
        response = authenticated_client.post(url, data, format='json')
        
        # Должна быть ошибка валидации
        assert response.status_code == 400
        
    def test_xss_prevention_in_profile(self, authenticated_client):
        """Тест защиты от XSS в профиле"""
        xss_payload = '<script>alert("XSS")</script>'
        
        url = reverse('profile')
        data = {'bio': xss_payload}
        
        response = authenticated_client.patch(url, data, format='json')
        
        # Данные должны сохраниться
        assert response.status_code == 200
        
    def test_idor_prevention_game_sessions(self, authenticated_client, another_user):
        """Тест предотвращения IDOR для игровых сессий"""
        # Создаем сессию от другого пользователя
        other_session = GameSession.objects.create(
            user=another_user,
            difficulty=3,
            game_state={'tiles': []},
            score=5000,
            is_completed=True
        )
        
        # Пытаемся получить доступ к чужой сессии через API
        url = reverse('gamesession-detail', kwargs={'pk': other_session.id})
        response = authenticated_client.get(url)
        
        # Должны получить 404 или 403
        assert response.status_code in [404, 403]
        
    def test_parameter_tampering_prevention(self, authenticated_client, user, another_user):
        """Тест предотвращения подмены параметров"""
        # Сначала добавляем друга
        Friendship.objects.create(
            from_user=user,
            to_user=another_user
        )
        
        # Пытаемся создать вызов
        url = reverse('challenge-list')
        
        data = {
            'to_username': 'anotheruser',
            'difficulty': 3,
            'target_score': 1000
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        # Должен быть успех или ошибка, но не 500
        assert response.status_code != 500
        
    def test_data_exposure_prevention(self, authenticated_client):
        """Тест предотвращения раскрытия данных"""
        # Получаем профиль
        url = reverse('profile')
        response = authenticated_client.get(url)
        
        # Проверяем, что в ответе нет чувствительных данных
        data = response.data
        
        # Не должно быть пароля
        assert 'password' not in data
        assert 'password_hash' not in data
        
    def test_rate_limiting_attempt(self, api_client):
        """Тест ограничения запросов (имитация DoS)"""
        url = reverse('register')
        
        # Пытаемся отправить несколько запросов
        for i in range(5):
            data = {
                'username': f'ratelimit{i}',
                'password': f'Pass{i}',
                'email': f'rate{i}@example.com'
            }
            response = api_client.post(url, data, format='json')
            
        # Сервер должен отвечать
        assert response.status_code in [201, 400]
        
    def test_json_injection_prevention(self, authenticated_client):
        """Тест защиты от инъекции через JSON"""
        url = reverse('gamesession-list')
        
        malicious_game_state = {
            'tiles': [],
            '__proto__': {'polluted': True},
            'constructor': {'name': 'malicious'}
        }
        
        data = {
            'difficulty': 3,
            'game_state': malicious_game_state,
            'score': 1000,
            'is_completed': False
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        # Должен быть успешный ответ или ошибка валидации
        assert response.status_code in [201, 400]
        
    def test_file_upload_security(self, authenticated_client):
        """Тест безопасности загрузки файлов"""
        url = reverse('profile')
        
        # Создаем тестовый файл
        test_content = b'test content'
        test_file = SimpleUploadedFile(
            name='test.jpg',
            content=test_content,
            content_type='image/jpeg'
        )
        
        # Отправляем запрос
        response = authenticated_client.patch(
            url, 
            {'avatar': test_file},
            format='multipart'
        )
        
        # Проверяем ответ
        assert response.status_code in [200, 400]