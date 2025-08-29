from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'painel_entregador'

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('logout/', LogoutView.as_view(next_page='painel_entregador:login'), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Pedidos
    path('pedidos-disponiveis/', views.pedidos_disponiveis, name='pedidos_disponiveis'),
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('pedido/<uuid:pedido_id>/', views.detalhe_pedido, name='detalhe_pedido'),
    
    # Actions AJAX
    path('aceitar-pedido/<uuid:pedido_id>/', views.aceitar_pedido, name='aceitar_pedido'),
    path('alterar-status/<uuid:pedido_id>/', views.alterar_status_pedido, name='alterar_status_pedido'),
    path('registrar-ocorrencia/<uuid:pedido_id>/', views.registrar_ocorrencia, name='registrar_ocorrencia'),
    path('alterar-disponibilidade/', views.alterar_disponibilidade, name='alterar_disponibilidade'),
    
    # Perfil e gestão
    path('perfil/', views.perfil, name='perfil'),
    path('avaliacoes/', views.avaliacoes, name='avaliacoes'),
    path('relatorios/', views.relatorios, name='relatorios'),
]