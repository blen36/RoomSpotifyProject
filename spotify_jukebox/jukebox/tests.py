from django.test import TestCase
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Room


# --- ТЕСТЫ МОДЕЛЕЙ (База Данных) ---

@pytest.mark.django_db
def test_create_room_model():
    """
    Тест проверяет, что комната успешно создается в БД
    и автоматически получает уникальный код.
    """
    # 1. Создаем пользователя (хоста)
    host_user = User.objects.create_user(username='test_host', password='password123')

    # 2. Создаем комнату
    room = Room.objects.create(
        host=host_user,
        guest_can_pause=True,
        votes_to_skip=3
    )

    # 3. Проверки (Asserts)
    assert room.code is not None  # Код должен сгенерироваться сам
    assert len(room.code) == 4  # Длина кода должна быть 4 символа (как в твоей функции)
    assert room.host == host_user  # Хост должен быть привязан
    assert room.guest_can_pause is True  # Настройки должны сохраниться
    assert room.votes_to_skip == 3


@pytest.mark.django_db
def test_room_string_representation():
    """
    Проверяет, что строковое представление объекта (то, что видно в админке)
    выглядит красиво: "Room ABCD (username)"
    """
    user = User.objects.create_user(username='admin')
    room = Room.objects.create(host=user, code='ABCD')

    expected_string = "Room ABCD (admin)"
    assert str(room) == expected_string


# --- ТЕСТЫ VIEWS (Логика Создания и Входа) ---

@pytest.mark.django_db
def test_create_room_view(client):
    """
    Тест проверяет, может ли авторизованный пользователь
    создать комнату через форму на сайте.
    """
    # 1. Логинимся
    user = User.objects.create_user(username='creator', password='password')
    client.force_login(user)

    # 2. Имитируем отправку формы создания комнаты (POST запрос)
    url = reverse('create_room')  # Убедись, что в urls.py этот путь называется 'create_room'
    data = {
        'guest_can_pause': True,
        'votes_to_skip': 2
    }
    response = client.post(url, data)

    # 3. Проверяем результат
    # Должен быть редирект (код 302) на страницу комнаты
    assert response.status_code == 302

    # Проверяем, что комната реально появилась в базе
    room = Room.objects.get(host=user)
    assert room.votes_to_skip == 2


@pytest.mark.django_db
def test_join_room_view_success(client):
    """
    Тест проверяет успешный вход в существующую комнату.
    """
    # 1. Подготовка: создаем комнату заранее
    host = User.objects.create_user(username='host')
    existing_room = Room.objects.create(host=host, code='TEST')

    # 2. Логинимся другим юзером (гостем)
    guest = User.objects.create_user(username='guest', password='password')
    client.force_login(guest)

    # 3. Отправляем код комнаты
    url = reverse('join_room')
    response = client.post(url, {'code': 'TEST'})

    # 4. Проверяем, что нас перенаправило (302) и в сессии записался код
    assert response.status_code == 302
    assert client.session['room_code'] == 'TEST'


@pytest.mark.django_db
def test_join_room_view_failure(client):
    """
    Тест проверяет, что будет, если ввести неправильный код.
    """
    user = User.objects.create_user(username='user', password='password')
    client.force_login(user)

    url = reverse('join_room')
    response = client.post(url, {'code': 'WRONG'})

    # Мы должны остаться на той же странице (код 200), а не редиректнуться
    assert response.status_code == 200
    # В контенте страницы должна быть ошибка
    assert "Комната не найдена" in response.content.decode('utf-8')

# Create your tests here.
