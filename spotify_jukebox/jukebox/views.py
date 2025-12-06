from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Room
from .forms import CreateRoomForm, JoinRoomForm


def home(request):
    """Главная страница: выбор (Создать или Войти)"""
    return render(request, 'jukebox/home.html')


@login_required(login_url='/admin/login/')  # Пока отправляем в админку, если не вошел, позже сделаем норм вход
def create_room(request):
    """Логика создания комнаты"""
    if request.method == 'POST':
        form = CreateRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()

            # ВАЖНО: Запоминаем в сессии, что этот юзер сидит в этой комнате
            request.session['room_code'] = room.code
            return redirect('room', room_code=room.code)
    else:
        form = CreateRoomForm()

    return render(request, 'jukebox/create_room.html', {'form': form})


def join_room(request):
    """Логика входа в существующую комнату"""
    if request.method == 'POST':
        form = JoinRoomForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if Room.objects.filter(code=code).exists():
                request.session['room_code'] = code
                return redirect('room', room_code=code)
            else:
                return render(request, 'jukebox/join_room.html', {
                    'form': form,
                    'error': 'Комната не найдена!'
                })
    else:
        form = JoinRoomForm()

    return render(request, 'jukebox/join_room.html', {'form': form})


def room(request, room_code):
    """Страница самой комнаты"""
    room_qs = Room.objects.filter(code=room_code)

    if room_qs.exists():
        room = room_qs.first()
        is_host = room.host == request.user
        context = {
            'room': room,
            'is_host': is_host,
        }
        return render(request, 'jukebox/room.html', context)
    else:
        return redirect('home')