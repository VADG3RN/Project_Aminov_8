#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'puzzle_backend.settings')

# Добавляем текущую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Инициализируем Django
django.setup()

# Теперь можно импортировать модели
from django.contrib.auth.models import User

# Простой тест
print("Создаем тестового пользователя...")
user = User.objects.create_user(
    username='debuguser',
    password='debugpass123'
)
print(f"Пользователь создан: {user.username}, ID: {user.id}")

# Проверяем создание профиля
from game.models import UserProfile
profile = UserProfile.objects.get(user=user)
print(f"Профиль создан автоматически: {profile.id}")

print("Тест завершен успешно!")