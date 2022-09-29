from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


handler404 = 'core.views.page_not_found'
handler500 = 'core.views.internal_server_error'


urlpatterns = [
    path('', include('posts.urls', namespace='posts')),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('about/', include('about.urls', namespace='about')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
