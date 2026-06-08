"""
URLs principais do projeto bar_escola
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from bar_app.views.auth import logout_view
from django.shortcuts import redirect

def admin_logout_view(request):
    logout_view(request)
    return redirect('admin:login')

urlpatterns = [
    # Custom logout to bypass Django 5.0+ POST requirement for admin
    path('admin/logout/', admin_logout_view, name='admin_logout'),
    path('admin/', admin.site.urls),
    path('', include('bar_app.urls')),
    path('captcha/', include('captcha.urls')),
    path('service-worker.js', TemplateView.as_view(template_name="service-worker.js", content_type="application/javascript"), name="service-worker.js"),
]

# Servir arquivos de média em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
