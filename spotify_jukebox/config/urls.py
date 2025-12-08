from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('spotify/', include('jukebox.urls')),
    path('', include('jukebox.urls'))
]