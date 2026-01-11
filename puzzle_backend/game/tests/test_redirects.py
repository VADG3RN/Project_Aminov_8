import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestRedirects:
    """Тестирование редиректов"""
    
    def test_redirect_after_login_via_admin(self, client, admin_user):
        """Тест редиректа после входа в админку"""
        login_url = reverse('admin:login')
        
        # Пытаемся зайти без аутентификации
        response = client.get(reverse('admin:index'))
        assert response.status_code == 302  # Редирект на логин
        
        # Логинимся
        client.force_login(admin_user)
        
        # Теперь доступ должен быть
        response = client.get(reverse('admin:index'))
        assert response.status_code == 200
        
    def test_no_redirect_for_authenticated_api(self, api_client, user):
        """Тест: аутентифицированный API пользователь не редиректится"""
        api_client.force_authenticate(user=user)
        
        url = reverse('profile')
        response = api_client.get(url)
        
        # Должен быть прямой ответ, а не редирект
        assert response.status_code == 200
        assert not response.headers.get('Location')
        
    def test_redirect_for_unauthenticated_api(self, api_client):
        """Тест: неаутентифицированный API пользователь получает 401"""
        url = reverse('profile')
        response = api_client.get(url)
        
        # Для API должен быть 401, а не редирект
        assert response.status_code == status.HTTP_401_UNAUTHORIZED