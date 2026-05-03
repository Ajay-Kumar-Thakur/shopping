"""
URL configuration for mysite project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Language-switcher endpoint — MUST be outside i18n_patterns
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    prefix_default_language=False,   # /en/ prefix optional for default language
)

# Serve uploaded media files in development (DEBUG=True only)
# In production, your web server (nginx/apache) should serve MEDIA_ROOT directly.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)