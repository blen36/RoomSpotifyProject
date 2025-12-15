from rest_framework import serializers
from .models import Room

# Базовый сериализатор (превращает модель Room в JSON)
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ('id', 'code', 'host', 'guest_can_pause', 'votes_to_skip', 'created_at')

# Сериализатор для создания комнаты (обычно он тоже нужен)
class CreateRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ('guest_can_pause', 'votes_to_skip')

# --- ТОТ, ЧТО НУЖЕН СЕЙЧАС (Для обновления) ---
class UpdateRoomSerializer(serializers.ModelSerializer):
    # Переопределяем поле code, чтобы отключить проверку уникальности при поиске
    code = serializers.CharField(validators=[])

    class Meta:
        model = Room
        fields = ('guest_can_pause', 'votes_to_skip', 'code')