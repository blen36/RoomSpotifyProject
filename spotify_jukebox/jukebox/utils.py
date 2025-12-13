from datetime import timedelta
from django.utils import timezone
from requests import post, put, get
from django.conf import settings

# Основные URL Spotify API
BASE_URL = "https://api.spotify.com/v1/"
TOKEN_URL = "https://accounts.spotify.com/api/token"


# ==========================================
# 1. УПРАВЛЕНИЕ ТОКЕНАМИ
# ==========================================

def get_user_tokens(user):
    # ВАЖНО: Импорт внутри функции предотвращает ошибку Circular Import
    from .models import SpotifyToken

    user_tokens = SpotifyToken.objects.filter(user=user)
    if user_tokens.exists():
        return user_tokens[0]
    return None


def update_or_create_user_tokens(user, access_token, token_type, expires_in, refresh_token):
    from .models import SpotifyToken

    tokens = get_user_tokens(user)
    # Spotify возвращает время жизни в секундах, превращаем в дату
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
    from .models import SpotifyToken

    tokens = get_user_tokens(user)
    if tokens:
        expiry = tokens.expires_in
        if expiry <= timezone.now():
            refresh_spotify_token(user)
        return True
    return False


def refresh_spotify_token(user):
    from .models import SpotifyToken

    refresh_token = get_user_tokens(user).refresh_token

    try:
        response = post(TOKEN_URL, data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.SPOTIPY_CLIENT_ID,
            'client_secret': settings.SPOTIPY_CLIENT_SECRET
        }).json()

        access_token = response.get('access_token')
        token_type = response.get('token_type')
        expires_in = response.get('expires_in')
        # Если новый refresh_token не пришел, оставляем старый
        new_refresh_token = response.get('refresh_token', refresh_token)

        update_or_create_user_tokens(user, access_token, token_type, expires_in, new_refresh_token)
    except Exception as e:
        print(f"Error refreshing token: {e}")


# ==========================================
# 2. ФУНКЦИИ API (ПОИСК, ПЛЕЕР, ОЧЕРЕДЬ)
# ==========================================

def execute_spotify_api_request(host, endpoint, post_=False, put_=False, data=None):
    """
    Универсальная функция для отправки запросов к Spotify API
    """
    from .models import SpotifyToken

    tokens = get_user_tokens(host)
    if not tokens:
        return {'error': 'No tokens found'}

    headers = {'Content-Type': 'application/json', 'Authorization': "Bearer " + tokens.access_token}

    # Если endpoint уже содержит полный URL, используем его, иначе добавляем BASE_URL
    if endpoint.startswith("http"):
        url = endpoint
    else:
        url = BASE_URL + endpoint

    try:
        if post_:
            response = post(url, headers=headers, json=data)  # json=data автоматически ставит нужные заголовки
        elif put_:
            response = put(url, headers=headers, json=data)
        else:
            response = get(url, {}, headers=headers)

        # Пытаемся вернуть JSON, если ответ не пустой
        if response.content:
            return response.json()
        return {'Status': 'Success'}  # Если тело ответа пустое (например, при 204 No Content)
    except Exception as e:
        return {'Error': f'Issue with request: {str(e)}'}


def search_spotify(host_user, query):
    """
    Поиск треков
    """
    if not query:
        return []

    # Кодируем пробелы для URL
    query_formatted = query.replace(' ', '%20')
    endpoint = f"search?q={query_formatted}&type=track&limit=10"

    response = execute_spotify_api_request(host_user, endpoint)

    if 'error' in response or 'tracks' not in response:
        return []

    tracks = []
    items = response.get('tracks', {}).get('items', [])

    for item in items:
        # Собираем только нужные данные
        track = {
            'title': item.get('name'),
            'artist': ", ".join([artist.get('name') for artist in item.get('artists', [])]),
            'uri': item.get('uri'),
            'image_url': item.get('album', {}).get('images', [{}])[0].get('url'),
            'id': item.get('id')
        }
        tracks.append(track)

    return tracks


def add_to_queue(host_user, track_uri):
    """
    Добавить трек в очередь
    """
    endpoint = f"me/player/queue?uri={track_uri}"
    return execute_spotify_api_request(host_user, endpoint, post_=True)


def get_current_song(host):
    """
    Получить текущий трек + данные о голосовании
    """
    # Импортируем модели Room и Vote здесь, чтобы избежать ошибки импорта
    from .models import Room, Vote

    endpoint = "me/player/currently-playing"
    response = execute_spotify_api_request(host, endpoint)

    # Проверка на ошибку или отсутствие активного устройства
    if 'error' in response or 'item' not in response:
        return {'error': 'No Active Device'}

    item = response.get('item')
    if not item:
        return {'error': 'No music playing'}

    duration = item.get('duration_ms')
    progress = response.get('progress_ms')
    album_cover = item.get('album', {}).get('images', [{}])[0].get('url')
    is_playing = response.get('is_playing')
    song_id = item.get('id')

    # Формируем строку авторов (Artist 1, Artist 2)
    artist_string = ""
    for i, artist in enumerate(item.get('artists')):
        if i > 0:
            artist_string += ", "
        artist_string += artist.get('name')

    # === ЛОГИКА ГОЛОСОВАНИЯ ===
    votes = 0
    votes_required = 0

    try:
        room = Room.objects.get(host=host)
        votes_required = room.votes_to_skip
        votes = Vote.objects.filter(room=room, song_id=song_id).count()
    except:
        pass

    song = {
        'title': item.get('name'),
        'artist': artist_string,
        'duration': duration,
        'time': progress,
        'image_url': album_cover,
        'is_playing': is_playing,
        'votes': votes,
        'votes_required': votes_required,
        'id': song_id
    }

    return song