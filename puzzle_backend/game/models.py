from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta

class TimeStampedModel(models.Model):
    """Абстрактная модель с таймстемпами."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserProfile(TimeStampedModel):
    """Профиль пользователя с дополнительными полями."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, verbose_name="О себе")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")

    def __str__(self):
        return f"Профиль {self.user.username}"

class Achievement(TimeStampedModel):
    """Достижение (награда)."""
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    icon = models.ImageField(upload_to='achievements/', blank=True, null=True, verbose_name="Иконка")

    def __str__(self):
        return self.name

class UserAchievement(TimeStampedModel):
    """Связь пользователя и достижения (многие-ко-многим)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'achievement')
        verbose_name = "Достижение пользователя"
        verbose_name_plural = "Достижения пользователей"

    def __str__(self):
        return f"{self.user.username} — {self.achievement.name}"

class GameSession(TimeStampedModel):
    """Сохранение игрового прогресса."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    difficulty = models.IntegerField(choices=[(3, '3x3'), (4, '4x4'), (5, '5x5')], verbose_name="Сложность")
    game_state = models.JSONField(verbose_name="Состояние игры")
    score = models.IntegerField(default=0, verbose_name="Очки")
    time_played = models.DurationField(null=True, blank=True, verbose_name="Время игры")
    is_completed = models.BooleanField(default=False, verbose_name="Завершена")

    def save(self, *args, **kwargs):
    # Сохраняем оригинальный created_at при первом сохранении
        if self.pk is None:
            # При создании записи
            super().save(*args, **kwargs)
            original_created_at = self.created_at
        else:
            # При обновлении получаем текущий объект из БД
            try:
                original = GameSession.objects.get(pk=self.pk)
                original_created_at = original.created_at
            except GameSession.DoesNotExist:
                original_created_at = self.created_at
            super().save(*args, **kwargs)
        
        # Обновляем время игры только если игра завершена и time_played еще не установлен
        if self.is_completed and self.time_played is None:
            # Используем текущее время для расчета
            from django.utils import timezone
            self.time_played = timezone.now() - original_created_at
            # Сохраняем без вызова сигнала save
            super(GameSession, self).save(update_fields=['time_played'])
        
        if self.is_completed:
            self.update_leaderboard()
    
    def update_leaderboard(self):
        try:
            leaderboard = Leaderboard.objects.get(user=self.user)
            # Находим лучший результат среди всех завершенных игр пользователя
            best_game = GameSession.objects.filter(
                user=self.user, 
                is_completed=True, 
                score__gt=0  # Только положительные результаты
            ).order_by('-score').first()
            
            if best_game and best_game.score > leaderboard.best_score:
                leaderboard.best_score = best_game.score
                leaderboard.date_achieved = best_game.updated_at
                leaderboard.save()
        except Leaderboard.DoesNotExist:
            # Создаем Leaderboard, если его нет
            Leaderboard.objects.create(
                user=self.user,
                best_score=self.score if self.is_completed else 0
            )

    def __str__(self):
        status = "завершена" if self.is_completed else "в процессе"
        return f"{self.user.username} — {self.difficulty}x{self.difficulty} ({status})"

class Friendship(TimeStampedModel):
    """Дружба (односторонняя или двусторонняя по логике)."""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends_out')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends_in')

    class Meta:
        unique_together = ('from_user', 'to_user')
        verbose_name = "Дружба"
        verbose_name_plural = "Друзья"

    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username}"

class Leaderboard(TimeStampedModel):
    """Лучший результат пользователя (обновляется при новом рекорде)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard')
    best_score = models.IntegerField(default=0, verbose_name="Лучшие очки")
    date_achieved = models.DateTimeField(null=True, blank=True, verbose_name="Дата достижения")

    def __str__(self):
        return f"Рекорд {self.user.username}: {self.best_score}"

class Challenge(TimeStampedModel):
    """Вызов другу."""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_challenges')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_challenges')
    difficulty = models.IntegerField(choices=[(3, '3x3'), (4, '4x4'), (5, '5x5')], verbose_name="Сложность")
    target_score = models.IntegerField(verbose_name="Цель (очки)")
    message = models.TextField(blank=True, verbose_name="Сообщение")
    is_accepted = models.BooleanField(default=False, verbose_name="Принят")
    is_completed = models.BooleanField(default=False, verbose_name="Завершён")
    response_score = models.IntegerField(null=True, blank=True, verbose_name="Ответ (очки)")

    def __str__(self):
        return f"Вызов от {self.from_user} к {self.to_user} ({self.difficulty}x{self.difficulty})"

# Сигналы для автосоздания профиля
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=User)
def create_user_leaderboard(sender, instance, created, **kwargs):
    if created:
        Leaderboard.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_leaderboard(sender, instance, **kwargs):
    if hasattr(instance, 'leaderboard'):
        instance.leaderboard.save()