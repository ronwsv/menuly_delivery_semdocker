from django.urls import path
from . import views

app_name = 'loja'

urlpatterns = [
    # Página inicial da loja
    path('', views.HomeView.as_view(), name='home'),
    
    # Cardápio
    path('cardapio/', views.CardapioView.as_view(), name='cardapio'),
    path('categoria/<slug:categoria_slug>/', views.CategoriaView.as_view(), name='categoria'),
    path('produto/<slug:produto_slug>/', views.ProdutoDetalheView.as_view(), name='produto_detalhe'),
    
    # Busca
    path('buscar/', views.BuscarProdutosView.as_view(), name='buscar'),
    
    # Carrinho
    path('carrinho/', views.CarrinhoView.as_view(), name='carrinho'),
    path('carrinho/adicionar/', views.AdicionarCarrinhoView.as_view(), name='adicionar_carrinho'),
    path('carrinho/remover/<str:item_id>/', views.RemoverCarrinhoView.as_view(), name='remover_carrinho'),
    path('carrinho/remover/', views.RemoverItemCarrinhoView.as_view(), name='remover_item_carrinho'),
    path('carrinho/alterar-quantidade/', views.AlterarQuantidadeCarrinhoView.as_view(), name='alterar_quantidade_carrinho'),
    path('carrinho/limpar/', views.LimparCarrinhoAjaxView.as_view(), name='limpar_carrinho'),
    
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('confirmacao-pedido/', views.ConfirmarPedidoView.as_view(), name='confirmacao_pedido'),
    
    # Pedidos
    path('pedido/<uuid:pedido_id>/', views.DetalhesPedidoView.as_view(), name='detalhes_pedido'),
    path('acompanhar/<str:numero_pedido>/', views.AcompanharPedidoView.as_view(), name='acompanhar_pedido'),
    
    # Cliente
    path('meus-pedidos/', views.MeusPedidosView.as_view(), name='meus_pedidos'),
    path('acessar-pedidos/', views.AcessarPedidosView.as_view(), name='acessar_pedidos'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    
    # Páginas institucionais
    path('sobre/', views.SobreView.as_view(), name='sobre'),
    path('contato/', views.ContatoView.as_view(), name='contato'),
    
    # APIs para funcionalidades dinâmicas
    path('api/buscar-cep/', views.BuscarCEPView.as_view(), name='api_buscar_cep'),
    path('api/calcular-entrega/', views.CalcularEntregaView.as_view(), name='api_calcular_entrega'),
]
