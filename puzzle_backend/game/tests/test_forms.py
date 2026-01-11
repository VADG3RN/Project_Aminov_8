import pytest
from django.test import TestCase
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from game.models import UserProfile, GameSession
import json

@pytest.mark.django_db
class TestForms(TestCase):
    """Тестирование форм (валидация данных)"""
    
    def test_user_creation_form_valid(self):
        """Тест валидной формы создания пользователя"""
        form_data = {
            'username': 'formuser',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        # Используем форму UserCreationForm (без email, так как она не обязательна)
        form = UserCreationForm(data=form_data)
        assert form.is_valid() is True
        
        # Сохраняем пользователя
        user = form.save()
        assert user.username == 'formuser'
        
    def test_user_creation_form_invalid_password(self):
        """Тест невалидной формы (пароли не совпадают)"""
        form_data = {
            'username': 'formuser2',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass!',
        }
        
        form = UserCreationForm(data=form_data)
        assert form.is_valid() is False
        assert 'password2' in form.errors
        
    def test_user_creation_form_short_password(self):
        """Тест невалидной формы (короткий пароль)"""
        form_data = {
            'username': 'formuser3',
            'password1': '123',
            'password2': '123',
        }
        
        form = UserCreationForm(data=form_data)
        assert form.is_valid() is False
        assert 'password2' in form.errors
        
    def test_authentication_form_valid(self):
        """Тест валидной формы аутентификации"""
        # Сначала создаем пользователя
        user = User.objects.create_user(
            username='authuser',
            password='AuthPass123!'
        )
        
        form_data = {
            'username': 'authuser',
            'password': 'AuthPass123!'
        }
        
        form = AuthenticationForm(data=form_data)
        assert form.is_valid() is True
        
    def test_authentication_form_invalid(self):
        """Тест невалидной формы аутентификации"""
        form_data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        
        form = AuthenticationForm(data=form_data)
        assert form.is_valid() is False
        
    def test_game_session_json_validation(self):
        """Тест валидации JSON поля game_state"""
        from game.models import GameSession
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(
            username='jsonuser',
            password='jsonpass'
        )
        
        # Валидный JSON
        valid_game_state = {
            'tiles': [{'index': i} for i in range(9)],
            'moves': 10,
            'timer': 60
        }
        
        session = GameSession.objects.create(
            user=user,
            difficulty=3,
            game_state=valid_game_state,
            score=1000,
            is_completed=False
        )
        
        assert isinstance(session.game_state, dict)
        assert 'tiles' in session.game_state
        
        # Невалидный JSON (но JSONField может принимать строку)
        invalid_game_state = "not a json"
        
        try:
            session2 = GameSession.objects.create(
                user=user,
                difficulty=3,
                game_state=invalid_game_state,
                score=1000,
                is_completed=False
            )
            # Если дошло сюда, значит JSONField принял строку
            # Проверяем, что сохранилось как строка
            assert isinstance(session2.game_state, str)
        except Exception as e:
            # Если возникает ошибка, проверяем что это ошибка валидации
            assert 'game_state' in str(e)