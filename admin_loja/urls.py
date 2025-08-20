from django.urls import path
from . import views

app_name = 'admin_loja'

urlpatterns = [
    path('login/', views.admin_loja_login, name='login'),
    path('dashboard/', views.admin_loja_dashboard, name='dashboard'),
    path('pedidos/', views.admin_loja_pedidos, name='pedidos'),
    path('relatorios/', views.admin_loja_relatorios, name='relatorios'),
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
    
    # URLs para categorias
    path('categorias/', views.admin_loja_categorias, name='categorias'),
    path('categorias/cadastrar/', views.admin_loja_categoria_cadastrar, name='categoria_cadastrar'),
    path('categorias/<uuid:categoria_id>/editar/', views.admin_loja_categoria_editar, name='categoria_editar'),
    path('categorias/<uuid:categoria_id>/deletar/', views.admin_loja_categoria_deletar, name='categoria_deletar'),
    path('categorias/<uuid:categoria_id>/toggle-ativo/', views.admin_loja_categoria_toggle_ativo, name='categoria_toggle_ativo'),
    path('categorias/reorder/', views.admin_loja_categoria_reorder, name='categoria_reorder'),
    
    # URLs para produtos
    path('produtos/', views.admin_loja_produtos, name='produtos'),
    path('produtos/cadastrar/', views.admin_loja_produto_cadastrar, name='produto_cadastrar'),
    path('produtos/<uuid:produto_id>/editar/', views.admin_loja_produto_editar, name='produto_editar'),
    path('produtos/<uuid:produto_id>/deletar/', views.admin_loja_produto_deletar, name='produto_deletar'),
    path('produtos/<uuid:produto_id>/toggle-disponivel/', views.admin_loja_produto_toggle_disponivel, name='produto_toggle_disponivel'),
    path('produtos/<uuid:produto_id>/toggle-destaque/', views.admin_loja_produto_toggle_destaque, name='produto_toggle_destaque'),
    path('produtos/reorder/', views.admin_loja_produto_reorder, name='produto_reorder'),
    
    # URLs para gestão de equipe
    path('equipe/', views.equipe_listar, name='equipe_listar'),
    path('equipe/adicionar/', views.equipe_adicionar, name='equipe_adicionar'),
    path('equipe/<uuid:user_id>/editar/', views.equipe_editar, name='equipe_editar'),
    path('equipe/<uuid:user_id>/remover/', views.equipe_remover, name='equipe_remover'),
    
    path('', views.DashboardView.as_view(), name='dashboard-old'),
    path('logout/', views.admin_loja_logout, name='logout'),
]
