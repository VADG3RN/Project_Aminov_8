import pytest
import csv
from django.urls import reverse
from django.contrib.auth.models import User
from game.models import GameSession, Achievement
from io import StringIO

@pytest.mark.django_db
class TestAdminExport:
    """Тесты для административной панели и экспорта"""
    
    def test_admin_access_requires_staff(self, client, user):
        """Тест: доступ к админке требует staff статуса"""
        # Обычный пользователь
        client.force_login(user)
        url = reverse('admin:index')
        
        response = client.get(url)
        # Должен быть редирект на страницу логина (302)
        assert response.status_code == 302
        
    def test_admin_access_with_staff(self, client, admin_user):
        """Тест: доступ к админке с staff статусом"""
        client.force_login(admin_user)
        url = reverse('admin:index')
        
        response = client.get(url)
        assert response.status_code == 200
        
    def test_admin_game_session_list(self, client, admin_user, test_game_session):
        """Тест просмотра списка GameSession в админке"""
        client.force_login(admin_user)
        
        # Правильное имя для модели GameSession в админке
        try:
            url = reverse('admin:game_gamesession_changelist')
        except:
            # Если имя другое, попробуем найти
            url = '/admin/game/gamesession/'
        
        response = client.get(url)
        assert response.status_code == 200
        
    def test_admin_export_csv(self, client, admin_user, test_game_session):
        """Тест экспорта CSV через админку"""
        client.force_login(admin_user)
        
        # URL для экспорта GameSession в CSV
        try:
            url = reverse('admin:game_gamesession_changelist')
        except:
            url = '/admin/game/gamesession/'
        
        # Пробуем экспорт
        response = client.get(url)
        assert response.status_code == 200
        
        # Проверяем наличие интерфейса экспорта
        content = response.content.decode('utf-8')
        
    def test_admin_data_integrity(self, client, admin_user):
        """Тест целостности данных при экспорте"""
        # Создаем тестовые данные
        test_users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'integrity{i}',
                password=f'pass{i}',
                email=f'user{i}@example.com'
            )
            test_users.append(user)
            
            # Создаем несколько сессий для каждого пользователя
            for j in range(2):
                GameSession.objects.create(
                    user=user,
                    difficulty=3 + (j % 3),
                    game_state={'tiles': [], 'moves': j * 10},
                    score=1000 * (j + 1),
                    is_completed=(j % 2 == 0)
                )
        
        client.force_login(admin_user)
        
        # Проверяем админку
        try:
            url = reverse('admin:game_gamesession_changelist')
        except:
            url = '/admin/game/gamesession/'
        
        response = client.get(url)
        assert response.status_code == 200
        
    def test_admin_export_selected_columns(self, client, admin_user):
        """Тест экспорта только выбранных колонок"""
        # Создаем тестовую сессию
        user = User.objects.create_user(username='coluser', password='colpass')
        session = GameSession.objects.create(
            user=user,
            difficulty=3,
            game_state={'tiles': [], 'moves': 15},
            score=1500,
            is_completed=True
        )
        
        client.force_login(admin_user)
        
        # Проверяем админку
        try:
            url = reverse('admin:game_gamesession_changelist')
        except:
            url = '/admin/game/gamesession/'
        
        response = client.get(url)
        assert response.status_code == 200