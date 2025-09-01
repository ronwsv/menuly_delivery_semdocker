from django.urls import path
from . import views
from . import views_entregadores

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
    path('produtos/<uuid:produto_id>/personalizar/', views.admin_loja_produto_personalizar, name='produto_personalizar'),
    path('produtos/<uuid:produto_id>/deletar/', views.admin_loja_produto_deletar, name='produto_deletar'),
    path('produtos/<uuid:produto_id>/toggle-disponivel/', views.admin_loja_produto_toggle_disponivel, name='produto_toggle_disponivel'),
    path('produtos/<uuid:produto_id>/toggle-destaque/', views.admin_loja_produto_toggle_destaque, name='produto_toggle_destaque'),
    path('produtos/reorder/', views.admin_loja_produto_reorder, name='produto_reorder'),
    
    # URLs para gestão de equipe
    path('equipe/', views.equipe_listar, name='equipe_listar'),
    path('equipe/adicionar/', views.equipe_adicionar, name='equipe_adicionar'),
    path('equipe/<uuid:user_id>/editar/', views.equipe_editar, name='equipe_editar'),
    path('equipe/<uuid:user_id>/remover/', views.equipe_remover, name='equipe_remover'),
    
    # APIs para notificações
    path('api/notificacoes/<uuid:notificacao_id>/marcar-lida/', views.api_marcar_notificacao_lida, name='api_marcar_notificacao_lida'),
    path('api/notificacoes/verificar/', views.api_verificar_notificacoes, name='api_verificar_notificacoes'),
    path('api/notificacoes/criar-sistema/', views.api_criar_notificacao_sistema, name='api_criar_notificacao_sistema'),
    
    # URLs para perfil do usuário
    path('perfil/', views.perfil_visualizar, name='perfil_visualizar'),
    path('perfil/editar/', views.perfil_editar, name='perfil_editar'),
    path('perfil/alterar-senha/', views.perfil_alterar_senha, name='perfil_alterar_senha'),
    
    # URLs para suporte e ajuda
    path('suporte/', views.suporte_index, name='suporte_index'),
    path('suporte/contato/', views.suporte_contato, name='suporte_contato'),
    path('suporte/api/chat/', views.suporte_chat_api, name='suporte_chat_api'),
    
    # URLs para gestão de planos
    path('planos/', views.planos_meu_plano, name='planos_meu_plano'),
    path('planos/comparar/', views.planos_comparar, name='planos_comparar'),
    path('planos/upgrade/', views.planos_solicitar_upgrade, name='planos_solicitar_upgrade'),
    path('planos/processar-upgrade/', views.processar_upgrade, name='processar_upgrade'),
    path('planos/atribuir-plano/', views.atribuir_plano, name='atribuir_plano'),
    path('planos/api/restaurantes-sem-plano/', views.listar_restaurantes_sem_plano, name='listar_restaurantes_sem_plano'),
    path('planos/historico/', views.planos_historico_uso, name='planos_historico_uso'),
    path('planos/api/verificar-limite/', views.planos_api_verificar_limite, name='planos_api_verificar_limite'),
    
    # URLs para gestão de entregadores
    path('entregadores/', views_entregadores.listar_entregadores, name='entregadores_listar'),
    path('entregadores/<int:entregador_id>/', views_entregadores.detalhe_entregador, name='entregadores_detalhe'),
    path('entregadores/pedidos-aguardando/', views_entregadores.pedidos_aguardando_entregador, name='pedidos_aguardando_entregador'),
    path('entregadores/atribuir/<int:pedido_id>/', views_entregadores.atribuir_entregador_manual, name='atribuir_entregador_manual'),
    path('entregadores/ocorrencias/', views_entregadores.ocorrencias_entrega, name='ocorrencias_entrega'),
    path('entregadores/ocorrencias/<int:ocorrencia_id>/resolver/', views_entregadores.resolver_ocorrencia, name='resolver_ocorrencia'),
    path('entregadores/relatorio/', views_entregadores.relatorio_entregas, name='relatorio_entregas'),
    
    path('', views.DashboardView.as_view(), name='dashboard-old'),
    path('logout/', views.admin_loja_logout, name='logout'),
]
