from django.urls import path
from . import views

app_name = 'admin_loja'

urlpatterns = [
    path('login/', views.admin_loja_login, name='login'),
    path('dashboard/', views.admin_loja_dashboard, name='dashboard'),
    path('pedidos/', views.admin_loja_pedidos, name='pedidos'),
    path('pedidos/<uuid:pedido_id>/', views.admin_loja_cupom_pedido, name='cupom_pedido'),
    path('pedidos/<uuid:pedido_id>/avancar/', views.admin_loja_avancar_status_pedido, name='avancar_status_pedido'),
    path('configurar-frete/', views.admin_loja_configurar_frete, name='configurar_frete'),
    path('personalizar-loja/', views.admin_loja_personalizar_loja, name='personalizar_loja'),
    
    # URLs para impressoras
    path('impressoras/', views.admin_loja_impressoras, name='impressoras'),
    path('impressoras/cadastrar/', views.admin_loja_impressora_cadastrar, name='impressora_cadastrar'),
    path('impressoras/<uuid:impressora_id>/editar/', views.admin_loja_impressora_editar, name='impressora_editar'),
    path('impressoras/<uuid:impressora_id>/deletar/', views.admin_loja_impressora_deletar, name='impressora_deletar'),
    path('impressoras/<uuid:impressora_id>/testar/', views.admin_loja_impressora_testar, name='impressora_testar'),
    
    path('', views.DashboardView.as_view(), name='dashboard-old'),
    path('logout/', views.admin_loja_logout, name='logout'),
]
