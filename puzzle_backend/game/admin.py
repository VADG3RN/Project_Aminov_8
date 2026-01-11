from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from import_export.formats.base_formats import XLSX, CSV
from .models import (
    UserProfile, Achievement, UserAchievement, GameSession,
    Friendship, Leaderboard, Challenge
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"

class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 1
    verbose_name = "Достижение"
    verbose_name_plural = "Достижения"

class GameSessionInline(admin.TabularInline):
    model = GameSession
    extra = 0
    fields = ('difficulty', 'score', 'is_completed', 'updated_at')
    readonly_fields = ('updated_at',)

class UserAdmin(BaseUserAdmin, ExportActionMixin):
    inlines = (UserProfileInline, UserAchievementInline, GameSessionInline)
    list_display = ('username', 'email', 'is_staff', 'date_joined')
    actions = ['export_admin_action']

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class GameSessionResource(resources.ModelResource):
    user__username = resources.Field(attribute='user__username', column_name='Игрок')
    difficulty = resources.Field(attribute='difficulty', column_name='Сложность')
    score = resources.Field(attribute='score', column_name='Очки')
    is_completed = resources.Field(attribute='is_completed', column_name='Завершена')
    time_played = resources.Field(attribute='time_played', column_name='Время игры')
    updated_at = resources.Field(attribute='updated_at', column_name='Обновлено')

    class Meta:
        model = GameSession
        fields = ('user__username', 'difficulty', 'score', 'is_completed', 'time_played', 'updated_at')
        export_order = ('user__username', 'difficulty', 'score', 'is_completed', 'time_played', 'updated_at')

    def dehydrate_player(self, obj):
        return obj.user.username if obj.user else ''

    def dehydrate_difficulty(self, obj):
        choices = {3: '3x3', 4: '4x4', 5: '5x5'}
        return choices.get(obj.difficulty, str(obj.difficulty))

    def dehydrate_score(self, obj):
        return obj.score

    def dehydrate_is_completed(self, obj):
        return 'Да' if obj.is_completed else 'Нет'

    def dehydrate_time_played(self, obj):
        if obj.time_played:
            return int(obj.time_played.total_seconds())
        return ''

    def dehydrate_updated_at(self, obj):
        return obj.updated_at.strftime('%d.%m.%Y %H:%M:%S') if obj.updated_at else ''

class GameSessionAdmin(ImportExportModelAdmin):
    resource_class = GameSessionResource
    formats = [XLSX, CSV]
    list_display = ('player', 'difficulty_display', 'score', 'is_completed', 'time_played_display', 'updated_at')
    list_filter = ('difficulty', 'is_completed', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('time_played', 'created_at', 'updated_at')

    def player(self, obj):
        return obj.user.username if obj.user else ''
    player.short_description = 'Игрок'

    def difficulty_display(self, obj):
        choices = {3: '3x3', 4: '4x4', 5: '5x5'}
        return choices.get(obj.difficulty, str(obj.difficulty))
    difficulty_display.short_description = 'Сложность'

    def time_played_display(self, obj):
        if obj.time_played:
            return str(obj.time_played)
        return ''
    time_played_display.short_description = 'Время игры'

admin.site.register(GameSession, GameSessionAdmin)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement')
    list_filter = ('achievement',)
    search_fields = ('user__username', 'achievement__name')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'created_at')
    search_fields = ('from_user__username', 'to_user__username')

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'best_score', 'date_achieved')
    search_fields = ('user__username',)
    list_filter = ('best_score',)
    ordering = ('-best_score',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(best_score__gt=0)

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'difficulty', 'target_score', 'is_accepted', 'is_completed')
    list_filter = ('difficulty', 'is_accepted', 'is_completed')
    search_fields = ('from_user__username', 'to_user__username')