from django.db import models
from django.contrib.auth.models import User
import string
import random


# --- Служебные функции ---

def generate_unique_code():
    """Генерирует уникальный 4-символьный код (цифры + буквы)."""
    length = 4
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Room.objects.filter(code=code).exists():
            return code


# --- Модели ---

class SpotifyToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    refresh_token = models.CharField(max_length=500)
    access_token = models.CharField(max_length=500)
    expires_in = models.DateTimeField()
    token_type = models.CharField(max_length=50)

    def __str__(self):
        return f"Token for {self.user.username}"


class Room(models.Model):
    code = models.CharField(
        max_length=8,
        default=generate_unique_code,
        unique=True,
        editable=False
    )
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_rooms')

    # Настройки комнаты
    guest_can_pause = models.BooleanField(default=False)
    votes_to_skip = models.IntegerField(default=1)  # Сколько голосов нужно для пропуска
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Кэш текущего трека (чтобы не долбить API каждую секунду)
    current_song = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Room {self.code} ({self.host.username})"


class Track(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tracks')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # Данные трека
    title = models.CharField(max_length=150)
    artist = models.CharField(max_length=150)
    spotify_uri = models.CharField(max_length=100)  # ID трека: spotify:track:xxxx
    album_cover_url = models.URLField(null=True, blank=True)  # <-- ВАЖНО: Картинка альбома!

    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} in {self.room.code}"