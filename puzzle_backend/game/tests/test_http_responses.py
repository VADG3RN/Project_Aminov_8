import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestHTTPResponses:
    """Тестирование HTTP ответов для разных типов пользователей"""
    
    def test_anonymous_user_responses(self, client):
        """Тест ответов для анонимного пользователя"""
        urls = [
            ('/', 200),  # Главная страница
            (reverse('register'), 405),  # GET на регистрацию (должен быть POST)
            (reverse('token-obtain'), 405),  # GET на получение токена (должен быть POST)
        ]
        
        for url, expected_status in urls:
            response = client.get(url)
            assert response.status_code == expected_status, f"URL: {url}"
            
    def test_authenticated_user_responses(self, authenticated_client):
        """Тест ответов для аутентифицированного пользователя"""
        urls = [
            (reverse('profile'), 200),
            (reverse('gamesession-list'), 200),
            (reverse('friends-list'), 200),
            (reverse('achievements'), 200),
            (reverse('leaderboard'), 200),
        ]
        
        for url, expected_status in urls:
            response = authenticated_client.get(url)
            assert response.status_code == expected_status, f"URL: {url}"
            
    def test_admin_user_responses(self, client, admin_user):
        """Тест ответов для администратора"""
        client.force_login(admin_user)
        
        urls = [
            (reverse('admin:index'), 200),
            ('/admin/auth/user/', 200),
            ('/admin/game/gamesession/', 200),
            ('/admin/game/achievement/', 200),
        ]
        
        for url, expected_status in urls:
            response = client.get(url)
            assert response.status_code == expected_status, f"URL: {url}"
            
    def test_404_responses(self, authenticated_client):
        """Тест ответов 404 для несуществующих ресурсов"""
        urls = [
            reverse('gamesession-detail', kwargs={'pk': 99999}),
            reverse('friend-delete', kwargs={'pk': 99999}),
            '/api/nonexistent/',
        ]
        
        for url in urls:
            response = authenticated_client.get(url)
            assert response.status_code in [404, 405], f"URL: {url}"
            
    def test_method_not_allowed_responses(self, authenticated_client):
        """Тест ответов 405 для неподдерживаемых методов"""
        urls_methods = [
            (reverse('profile'), 'PUT'),
            (reverse('gamesession-list'), 'PUT'),
            (reverse('register'), 'PUT'),
        ]
        
        for url, method in urls_methods:
            if method == 'PUT':
                response = authenticated_client.put(url, {}, format='json')
            elif method == 'DELETE':
                response = authenticated_client.delete(url)
            else:
                continue
                
            assert response.status_code == 405, f"URL: {url}, Method: {method}"