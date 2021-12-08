from django.conf import settings
from django.conf.urls import handler404, handler500
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

if settings.DEBUG:
    import debug_toolbar

urlpatterns = [
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path("", include('posts.urls')),
    path('about/', include('about.urls', namespace='about')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),) 

handler404 = "posts.views.page_not_found"
handler500 = "posts.views.server_error"
