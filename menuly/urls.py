"""
Sistema Multi-Site de Delivery - URLs principais

Estrutura de URLs:
- / -> Landing page do Menuly
- /sobre/ -> Página sobre o Menuly
- /contato/ -> Página de contato do Menuly
- /<slug:restaurante_slug>/ -> Páginas da loja (cardápio, etc.)
- /admin-loja/ -> Painel do lojista
- /superadmin/ -> Painel global
- /admin/ -> Django Admin
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import LandingView, SobreView, ContatoView

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Páginas institucionais do Menuly
    path("", LandingView.as_view(), name="landing_page"),
    path("sobre/", SobreView.as_view(), name="sobre_menuly"),
    path("contato/", ContatoView.as_view(), name="contato_menuly"),

    # Admin da Loja - Painel do lojista
    path("admin-loja/", include("admin_loja.urls")),
    
    # Superadmin - Painel global
    path("superadmin/", include("superadmin.urls")),

    # Loja - Frontend para clientes (estrutura hierárquica)
    # Esta deve ser a ÚLTIMA das URLs principais para não capturar as outras.
    path("<slug:restaurante_slug>/", include("loja.urls")),
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
