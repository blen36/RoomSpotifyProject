from django import forms
from .models import Room

class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['guest_can_pause', 'votes_to_skip']

class JoinRoomForm(forms.Form):
    code = forms.CharField(label='Code', max_length=8)