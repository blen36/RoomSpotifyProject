from datetime import timedelta
from django.utils import timezone
from .models import SpotifyToken
from django.conf import settings
from requests import post, put, get
import os


BASE_URL = "https://api.spotify.com/v1/me/"


def get_user_tokens(user):
    """Получает токены пользователя из БД, если они есть."""
    user_tokens = SpotifyToken.objects.filter(user=user)
    if user_tokens.exists():
        return user_tokens[0]
    return None


def update_or_create_user_tokens(user, access_token, token_type, expires_in, refresh_token):
    """Создает или обновляет запись SpotifyToken для пользователя."""
    tokens = get_user_tokens(user)

    # Spotify возвращает expires_in в секундах (обычно 3600).
    # Нам нужно превратить это в точное время в будущем.
    expires_in = timezone.now() + timedelta(seconds=expires_in)

    if tokens:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=['access_token', 'refresh_token', 'expires_in', 'token_type'])
    else:
        tokens = SpotifyToken(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            token_type=token_type
        )
        tokens.save()


def is_spotify_authenticated(user):
    """
    Проверяет, авторизован ли пользователь.
    Если токен истек, пытается его обновить.
    """
    tokens = get_user_tokens(user)
    if tokens:
        expiry = tokens.expires_in
        if expiry <= timezone.now():
            # Токен истек, обновляем
            refresh_spotify_token(user)
        return True
    return False


def refresh_spotify_token(user):
    refresh_token = get_user_tokens(user).refresh_token

    # ИСПРАВЛЕН URL
    response = post(SPOTIFY_TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIPY_CLIENT_ID,
        'client_secret': SPOTIPY_CLIENT_SECRET
    }).json()

    access_token = response.get('access_token')
    token_type = response.get('token_type')
    expires_in = response.get('expires_in')

    # Иногда новый refresh_token не приходит, используем старый
    new_refresh_token = response.get('refresh_token', refresh_token)

    update_or_create_user_tokens(user, access_token, token_type, expires_in, new_refresh_token)