from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api

router = DefaultRouter()
router.register(r'pedidos', views_api.PedidoViewSet, basename='pedidos')
router.register(r'entregadores', views_api.EntregadorViewSet, basename='entregadores')
router.register(r'avaliacoes-entregador', views_api.AvaliacaoEntregadorViewSet, basename='avaliacoes-entregador')
router.register(r'ocorrencias-entrega', views_api.OcorrenciaEntregaViewSet, basename='ocorrencias-entrega')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    # URLs adicionais específicas da API podem ser adicionadas aqui
]