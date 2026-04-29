

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls', namespace='users')),   # ← добавить
    path('auth/', include('django.contrib.auth.urls')),       # ← для сброса пароля и т.п.
    path('about/', include('about.urls', namespace='about')),
    path('', include('posts.urls', namespace='posts')),
    
]