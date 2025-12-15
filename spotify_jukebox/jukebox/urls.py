from django.urls import path
from . import views
from .views import (
    AuthURL,
    spotify_callback,
    IsAuthenticated,
    LeaveRoom,    # НОВЫЙ
    UpdateRoom,
    GetRoom# НОВЫЙ
)

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_room, name='create_room'),
    path('join/', views.join_room, name='join_room'),
    # Важный момент: теперь URL комнаты выглядит как /room/ABCD123/
    path('room/<str:room_code>/', views.room, name='room'),
    path('get-auth-url', AuthURL.as_view()),
    path('redirect', spotify_callback),
    path('is-authenticated', IsAuthenticated.as_view()),
    path('api/current-song', views.CurrentSong.as_view()),
    path('api/pause', views.PauseSong.as_view()),
    path('api/play', views.PlaySong.as_view()),
    path('api/skip', views.SkipSong.as_view()),
    path('api/spotify/search', views.SearchSong.as_view()),   # Поиск
    path('api/spotify/queue', views.AddToQueue.as_view()),    # Очередь
    path('api/spotify/vote', views.VoteToSkip.as_view()),     # Голосование
    path('leave-room', LeaveRoom.as_view()),
    path('update-room', UpdateRoom.as_view()),
    path('get-room', GetRoom.as_view()),
]