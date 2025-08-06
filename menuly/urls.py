"""
Sistema Multi-Site de Delivery - URLs principais

Estrutura de URLs:
- / -> Loja (Frontend para clientes)
- /admin-loja/ -> Painel do lojista
- /superadmin/ -> Painel global
- /admin/ -> Django Admin
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    
    # Loja - Frontend para clientes (estrutura hierárquica)
    path("<slug:restaurante_slug>/", include("loja.urls", namespace="loja_hierarquica")),
    
    # Loja - Frontend para clientes (raiz para compatibilidade)
    path("", include("loja.urls")),
    
    # Admin da Loja - Painel do lojista (prioridade 2)
    path("admin-loja/", include("admin_loja.urls")),
    
    # Superadmin - Painel global (prioridade 3)
    path("superadmin/", include("superadmin.urls")),
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
