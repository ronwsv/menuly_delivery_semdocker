from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.db import models
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import requests
import traceback
from decimal import Decimal, InvalidOperation

from core.models import (
    Restaurante, Categoria, Produto, Pedido, ItemPedido, 
    PersonalizacaoItemPedido, Usuario, Endereco, HistoricoStatusPedido
)


class BaseLojaView(TemplateView):
    """View base para todas as páginas da loja"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obter restaurante EXCLUSIVAMENTE pelo slug da URL.
        # Não deve haver fallback. Uma página de loja SEMPRE precisa de um restaurante.
        restaurante_slug = kwargs.get('restaurante_slug')
        if not restaurante_slug:
            # Se nenhum slug for fornecido, não há restaurante para mostrar.
            # Isso força a estrutura de URL correta.
            raise Http404("Restaurante não encontrado.")

        restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            
        context['restaurante'] = restaurante
        context['restaurante_atual'] = restaurante  # Para compatibilidade com templates
        
        # Categorias para o menu, com produtos pré-carregados para eficiência
        context['categorias_menu'] = restaurante.categorias.filter(ativo=True).prefetch_related(
            Prefetch('produtos', queryset=Produto.objects.filter(disponivel=True).order_by('ordem', 'nome'))
        ).order_by('ordem', 'nome')
        
        # Produtos em destaque
        context['produtos_destaque'] = restaurante.produtos.filter(
            destaque=True, 
            disponivel=True
        ).select_related('categoria')[:6]
        
        # Informações do carrinho
        context['carrinho_count'] = self.get_carrinho_count()
        
        return context
    
    def get_carrinho_count(self):
        """Retorna a quantidade de itens no carrinho"""
        carrinho = self.request.session.get('carrinho', {})
        return sum(item['quantidade'] for item in carrinho.values())


class HomeView(BaseLojaView):
    """Página inicial da loja"""
    template_name = 'loja/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if context['restaurante']:
            # Categorias para exibir na home
            context['categorias_home'] = context['restaurante'].categorias.filter(
                ativo=True
            ).order_by('ordem', 'nome')[:8]
            
            # Produtos mais pedidos/populares (simulando por enquanto)
            produtos_populares = context['restaurante'].produtos.filter(
                disponivel=True
            ).select_related('categoria').order_by('-created_at')[:8]
            
            context['produtos_populares'] = produtos_populares
            
            # Preparar dados dos produtos para JavaScript (carrinho)
            produtos_js = {}
            for produto in produtos_populares:
                preco_final = produto.preco_promocional if produto.tem_promocao else produto.preco
                produtos_js[str(produto.id)] = {
                    'id': produto.id,
                    'nome': produto.nome,
                    'preco': float(preco_final),
                    'categoria': produto.categoria.slug if produto.categoria else '',
                    'imagem': produto.imagem_principal.url if produto.imagem_principal else '/static/img/placeholder.jpg',
                    'disponivel': produto.disponivel
                }
            
            context['produtos_js'] = produtos_js
            print(f"🏠 HomeView: {len(produtos_populares)} produtos populares, dados JS preparados")
        
        return context


class CardapioView(BaseLojaView):
    """Página do cardápio completo"""
    template_name = 'loja/cardapio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # As categorias já foram carregadas na BaseLojaView com prefetch_related.
        # Apenas pegamos esses dados e preparamos para o template e JS.
        # O prefetch_related em BaseLojaView já garante que os produtos de cada
        # categoria sejam carregados de forma otimizada.
        categorias = context.get('categorias_menu', [])
        context['categorias_cardapio'] = categorias
        
        if categorias:
            # Preparar dados de TODOS os produtos para JavaScript (carrinho)
            produtos_js = {}
            todos_produtos = []
            for categoria in categorias:
                # Usar .all() aqui é eficiente por causa do prefetch_related na view base
                produtos_da_categoria = categoria.produtos.all()
                todos_produtos.extend(produtos_da_categoria)
                for produto in produtos_da_categoria:
                    preco_final = produto.preco_promocional if produto.tem_promocao else produto.preco
                    produtos_js[str(produto.id)] = {
                        'id': str(produto.id),
                        'nome': produto.nome,
                        'preco': float(preco_final),
                        'categoria': categoria.slug,
                        'imagem': produto.imagem_principal.url if produto.imagem_principal else '/static/img/placeholder.jpg',
                        'disponivel': produto.disponivel
                    }
            
            context['produtos_js'] = json.dumps(produtos_js)
            print(f"🍕 CardapioView (Otimizada): {len(categorias)} categorias, {len(todos_produtos)} produtos no total.")

        return context


class CategoriaView(BaseLojaView):
    """Página de uma categoria específica"""
    template_name = 'loja/categoria.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categoria_slug = kwargs.get('categoria_slug')
        
        if context['restaurante']:
            categoria = get_object_or_404(
                Categoria, 
                restaurante=context['restaurante'],
                slug=categoria_slug,
                ativo=True
            )
            
            produtos = categoria.produtos.filter(disponivel=True).order_by('ordem', 'nome')
            
            # Paginação
            paginator = Paginator(produtos, 12)
            page_number = self.request.GET.get('page')
            produtos_paginated = paginator.get_page(page_number)
            
            context['categoria'] = categoria
            context['produtos'] = produtos_paginated
        
        return context


class ProdutoDetalheView(BaseLojaView):
    """Página de detalhes do produto"""
    template_name = 'loja/produto_detalhe.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produto_slug = kwargs.get('produto_slug')
        
        if context['restaurante']:
            produto = get_object_or_404(
                Produto,
                restaurante=context['restaurante'],
                slug=produto_slug,
                disponivel=True
            )
            
            # Opções de personalização
            opcoes_personalizacao = produto.opcoes_personalizacao.filter(
                ativo=True
            ).prefetch_related('itens').order_by('ordem')
            
            # Produtos relacionados (da mesma categoria)
            produtos_relacionados = produto.categoria.produtos.filter(
                disponivel=True
            ).exclude(id=produto.id).order_by('ordem', 'nome')[:4]
            
            context['produto'] = produto
            context['opcoes_personalizacao'] = opcoes_personalizacao
            context['produtos_relacionados'] = produtos_relacionados
        
        return context


class BuscarProdutosView(BaseLojaView):
    """Busca de produtos"""
    template_name = 'loja/buscar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        
        if context['restaurante'] and query:
            produtos = context['restaurante'].produtos.filter(
                Q(nome__icontains=query) | 
                Q(descricao__icontains=query) |
                Q(categoria__nome__icontains=query),
                disponivel=True
            ).select_related('categoria').order_by('nome')
            
            # Paginação
            paginator = Paginator(produtos, 12)
            page_number = self.request.GET.get('page')
            produtos_paginated = paginator.get_page(page_number)
            
            context['produtos'] = produtos_paginated
            context['query'] = query
            context['total_resultados'] = produtos.count()
        
        return context


class CarrinhoView(BaseLojaView):
    """Página do carrinho"""
    template_name = 'loja/carrinho.html'
    
    def get(self, request, *args, **kwargs):
        # Se for requisição AJAX, retornar JSON
        if request.headers.get('Accept') == 'application/json':
            carrinho = request.session.get('carrinho', {})
            carrinho_count = sum(item['quantidade'] for item in carrinho.values())
            
            # Buscar detalhes dos produtos e preparar lista de itens
            itens_carrinho = []
            total_valor = 0
            
            for item_key, item in carrinho.items():
                try:
                    produto_id = item['produto_id']
                    produto = Produto.objects.get(id=produto_id)
                    subtotal = item['preco'] * item['quantidade']
                    total_valor += subtotal
                    
                    itens_carrinho.append({
                        'produto_id': produto_id,
                        'nome': produto.nome,
                        'categoria': produto.categoria.nome if produto.categoria else '',
                        'quantidade': item['quantidade'],
                        'preco_unitario': item['preco'],
                        'preco_total': subtotal,
                        'personalizacoes': item.get('personalizacoes', []),
                        'observacoes': item.get('observacoes', ''),
                        'item_key': item_key,
                    })
                except Produto.DoesNotExist:
                    continue
            
            # Dados do restaurante
            restaurante_data = None
            if hasattr(self, 'get_context_data'):
                context = super().get_context_data(**kwargs)
                restaurante = context.get('restaurante')
                if restaurante:
                    endereco_completo = f"{restaurante.logradouro}, {restaurante.numero}"
                    if restaurante.complemento:
                        endereco_completo += f", {restaurante.complemento}"
                    endereco_completo += f" - {restaurante.bairro}, {restaurante.cidade}/{restaurante.estado}"
                    
                    restaurante_data = {
                        'nome': restaurante.nome,
                        'endereco': endereco_completo,
                        'slug': restaurante.slug
                    }
            
            return JsonResponse({
                'carrinho_count': carrinho_count,
                'total_items': len(carrinho),
                'items': itens_carrinho,
                'total': total_valor,
                'restaurante': restaurante_data
            })
        
        # Caso contrário, renderizar template normal
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrinho = self.request.session.get('carrinho', {})
        
        itens_carrinho = []
        total = 0
        
        for item_key, item in carrinho.items():
            try:
                produto_id = item['produto_id']
                produto = Produto.objects.get(id=produto_id)
                subtotal = item['preco'] * item['quantidade']
                total += subtotal
                
                itens_carrinho.append({
                    'produto': produto,
                    'quantidade': item['quantidade'],
                    'preco': item['preco'],
                    'subtotal': subtotal,
                    'personalizacoes': item.get('personalizacoes', []),
                    'observacoes': item.get('observacoes', ''),
                    'item_key': item_key,
                })
            except Produto.DoesNotExist:
                continue
        
        context['itens_carrinho'] = itens_carrinho
        context['total_carrinho'] = total
        context['carrinho_count'] = sum(item['quantidade'] for item in carrinho.values())
        
        return context


class AdicionarCarrinhoView(View):
    """Adicionar produto ao carrinho via AJAX"""
    
    def post(self, request, *args, **kwargs):
        try:
            print(f"🛒 POST recebido para adicionar carrinho: {request.body}")
            
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            quantidade = int(data.get('quantidade', 1))
            personalizacoes = data.get('personalizacoes', [])
            observacoes = data.get('observacoes', '')
            
            print(f"📦 Dados recebidos: produto_id={produto_id}, quantidade={quantidade}")
            
            # Buscar o produto sem restrição de restaurante primeiro
            produto = get_object_or_404(Produto, id=produto_id, disponivel=True)
            print(f"✅ Produto encontrado: {produto.nome} - R$ {produto.preco_final}")
            
            # Calcular preço com personalizações
            preco_base = produto.preco_final
            preco_adicional = sum(float(p.get('preco', 0)) for p in personalizacoes)
            preco_total = preco_base + preco_adicional
            
            print(f"💰 Preços: base={preco_base}, adicional={preco_adicional}, total={preco_total}")
            
            # Obter carrinho da sessão
            carrinho = request.session.get('carrinho', {})
            
            # Chave única para o item (incluindo personalizações)
            item_key = f"{produto_id}_{hash(str(sorted(personalizacoes)))}"
            
            if item_key in carrinho:
                carrinho[item_key]['quantidade'] += quantidade
                print(f"📦 Quantidade atualizada para produto existente: {carrinho[item_key]['quantidade']}")
            else:
                carrinho[item_key] = {
                    'produto_id': str(produto_id),
                    'quantidade': quantidade,
                    'preco': float(preco_total),
                    'personalizacoes': personalizacoes,
                    'observacoes': observacoes,
                }
                print(f"🆕 Novo item adicionado ao carrinho: {item_key}")
            
            request.session['carrinho'] = carrinho
            request.session.modified = True
            
            # Calcular novo total do carrinho
            carrinho_count = sum(item['quantidade'] for item in carrinho.values())
            
            print(f"🛒 Carrinho atualizado: {carrinho_count} itens")
            
            return JsonResponse({
                'success': True,
                'message': 'Produto adicionado ao carrinho!',
                'carrinho_count': carrinho_count
            })
            
        except Exception as e:
            print(f"❌ Erro na AdicionarCarrinhoView: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'success': False,
                'message': f'Erro ao adicionar produto: {str(e)}'
            }, status=400)


class RemoverCarrinhoView(View):
    """Remover item do carrinho"""
    
    def post(self, request, restaurante_slug, item_id):
        carrinho = request.session.get('carrinho', {})
        
        if item_id in carrinho:
            del carrinho[item_id]
            request.session['carrinho'] = carrinho
            request.session.modified = True
            messages.success(request, 'Item removido do carrinho!')
        
        return redirect('loja:carrinho', restaurante_slug=restaurante_slug)


class LimparCarrinhoView(View):
    """Limpar todo o carrinho"""
    
    def post(self, request, restaurante_slug):
        request.session['carrinho'] = {}
        request.session.modified = True
        messages.success(request, 'Carrinho limpo!')
        return redirect('loja:carrinho', restaurante_slug=restaurante_slug)


class CheckoutView(BaseLojaView):
    """Página de checkout"""
    template_name = 'loja/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dados do carrinho (copiado da CarrinhoView)
        carrinho = self.request.session.get('carrinho', {})
        
        itens_carrinho = []
        total = 0
        
        for produto_id_key, item in carrinho.items():
            try:
                # Extrair o UUID do produto da chave (formato: uuid_hash)
                if '_' in produto_id_key:
                    produto_id = produto_id_key.split('_')[0]
                else:
                    produto_id = produto_id_key
                    
                produto = Produto.objects.get(id=produto_id)
                subtotal = item['preco'] * item['quantidade']
                total += subtotal
                
                itens_carrinho.append({
                    'produto': produto,
                    'quantidade': item['quantidade'],
                    'preco': item['preco'],
                    'subtotal': subtotal,
                    'personalizacoes': item.get('personalizacoes', []),
                    'observacoes': item.get('observacoes', ''),
                })
            except Produto.DoesNotExist:
                continue
        
        # Taxa de entrega
        taxa_entrega = 0
        if total > 0 and self.request.session.get('endereco_entrega'):
            taxa_entrega = context['restaurante'].taxa_entrega
        
        total_final = total + taxa_entrega
        
        context.update({
            'itens_carrinho': itens_carrinho,
            'total_carrinho': total,
            'taxa_entrega': taxa_entrega,
            'total_final': total_final,
            'carrinho_count': sum(item['quantidade'] for item in carrinho.values()),
        })
        
        # Se usuário logado, pegar endereços
        if self.request.user.is_authenticated:
            context['enderecos_usuario'] = self.request.user.enderecos.all()
        
        # Formas de pagamento disponíveis
        context['formas_pagamento'] = [
            ('dinheiro', 'Dinheiro'),
            ('cartao_credito', 'Cartão de Crédito'),
            ('cartao_debito', 'Cartão de Débito'),
            ('pix', 'PIX'),
        ]
        
        return context

    def post(self, request, *args, **kwargs):
        """Processa o pedido do checkout."""
        print(f"🛒 POST recebido no checkout: {request.POST}")
        
        data = request.POST
        carrinho_json = data.get('carrinho_json')
        carrinho = {}

        if carrinho_json:
            print(f"📦 carrinho_json recebido: {carrinho_json}")
            try:
                carrinho_lista = json.loads(carrinho_json)
                print(f"📋 carrinho_lista decodificada: {carrinho_lista}")
                
                # Debug: mostrar estrutura do primeiro item
                if carrinho_lista:
                    primeiro_item = carrinho_lista[0]
                    print(f"🔍 Estrutura do primeiro item: {primeiro_item}")
                    print(f"🔍 Chaves disponíveis: {list(primeiro_item.keys())}")
                
                carrinho_temp = {}
                for i, item in enumerate(carrinho_lista):
                    print(f"📦 Processando item {i+1}: {item}")
                    
                    # Usar produto_id que vem da API Django, não 'id'
                    produto_id = item.get('produto_id') or item.get('id')
                    if not produto_id:
                        print(f"⚠️ Item sem produto_id: {item}")
                        continue
                        
                    item_key = f"{produto_id}"
                    carrinho_temp[item_key] = {
                        'produto_id': produto_id,
                        'nome': item.get('nome', ''),
                        'preco': Decimal(str(item.get('preco_unitario', item.get('preco', '0')))),
                        'quantidade': int(item.get('quantidade', 1)),
                        'observacoes': item.get('observacoes', ''),
                        'personalizacoes': item.get('personalizacoes', [])
                    }
                carrinho = carrinho_temp
                print(f"✅ Carrinho processado: {len(carrinho)} itens")
            except (json.JSONDecodeError, InvalidOperation):
                messages.error(request, "Ocorreu um erro ao processar os itens do seu carrinho (JSON inválido). Por favor, tente novamente.")
                return redirect('loja:carrinho', restaurante_slug=kwargs.get('restaurante_slug'))
            except (ValueError, TypeError, KeyError) as e:
                messages.error(request, f"Um item no seu carrinho está com dados inválidos: {e}. Por favor, verifique os itens no carrinho.")
                return redirect('loja:carrinho', restaurante_slug=kwargs.get('restaurante_slug'))

        if not carrinho:
            carrinho = request.session.get('carrinho', {})
            print(f"🔄 Usando carrinho da sessão: {len(carrinho)} itens")

        try:
            # Obter restaurante diretamente pelos kwargs, não via get_context_data
            restaurante_slug = kwargs.get('restaurante_slug')
            if not restaurante_slug:
                messages.error(request, 'Restaurante não identificado.')
                return redirect('landing_page')
                
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            print(f"🏪 Restaurante encontrado: {restaurante.nome}")

            if not carrinho:
                messages.error(request, 'Seu carrinho está vazio.')
                return redirect('loja:carrinho', restaurante_slug=restaurante_slug)

            tipo_entrega = data.get('tipo_entrega')
            taxa_entrega = 0
            if tipo_entrega == 'delivery' and restaurante:
                taxa_entrega = restaurante.taxa_entrega

            # Lógica para encontrar ou criar o cliente
            cliente_celular = ''.join(filter(str.isdigit, data.get('celular', '').strip()))
            cliente_instance = None

            if request.user.is_authenticated:
                cliente_instance = request.user
            elif cliente_celular:
                # Busca por celular ou email
                usuario = None
                email = data.get('email', '').strip()
                nome = data.get('nome', '').strip()
                try:
                    if email:
                        usuario = Usuario.objects.filter(email=email).first()
                    if not usuario:
                        usuario = Usuario.objects.filter(celular=cliente_celular).first()
                except Exception:
                    usuario = None

                if usuario:
                    # Atualiza nome se necessário
                    if nome and usuario.first_name != nome:
                        usuario.first_name = nome
                        usuario.save(update_fields=['first_name'])
                    cliente_instance = usuario
                else:
                    # Gera username único
                    base_username = email.split('@')[0] if email else cliente_celular.replace('+','').replace('-','').replace('(','').replace(')','').replace(' ','')
                    username = base_username
                    from core.models import Usuario
                    i = 1
                    while Usuario.objects.filter(username=username).exists():
                        username = f"{base_username}{i}"
                        i += 1
                    usuario = Usuario.objects.create(
                        username=username,
                        first_name=nome,
                        email=email,
                        celular=cliente_celular,
                        is_active=True,
                    )
                    usuario.set_unusable_password()
                    usuario.save()
                    cliente_instance = usuario

            pedido = Pedido.objects.create(
                restaurante=restaurante,
                cliente=cliente_instance,
                cliente_nome=data.get('nome'),
                cliente_celular=cliente_celular,
                cliente_email=data.get('email', ''),
                tipo_entrega=tipo_entrega,
                forma_pagamento=data.get('forma_pagamento'),
                observacoes=data.get('observacoes', ''),
                taxa_entrega=taxa_entrega,
                status='novo'
            )

            if data.get('forma_pagamento') == 'dinheiro':
                troco_para_str = data.get('troco_para', '0').replace(',', '.')
                if troco_para_str:
                    try:
                        pedido.troco_para = float(troco_para_str)
                    except (ValueError, TypeError):
                        messages.error(request, 'Valor de troco inválido.')
                        return self.get(request, *args, **kwargs)

            if pedido.tipo_entrega == 'delivery':
                pedido.endereco_logradouro = data.get('logradouro', '')
                pedido.endereco_numero = data.get('numero', '')
                pedido.endereco_complemento = data.get('complemento', '')
                pedido.endereco_bairro = data.get('bairro', '')
                pedido.endereco_cidade = data.get('cidade', '')
                pedido.endereco_estado = data.get('estado', '')
                pedido.endereco_cep = data.get('cep', '')
                pedido.endereco_ponto_referencia = data.get('ponto_referencia', '')

            total_pedido = Decimal('0.0')
            for produto_id_key, item_data in carrinho.items():
                try:
                    # Extrair o UUID do produto da chave (formato: uuid_hash)
                    if '_' in produto_id_key:
                        produto_id = produto_id_key.split('_')[0]
                    else:
                        produto_id = produto_id_key
                    
                    produto = Produto.objects.get(id=produto_id)
                    
                    # Garantir que os cálculos são feitos com Decimal
                    preco_unitario = Decimal(str(item_data.get('preco', '0')))
                    quantidade = Decimal(str(item_data.get('quantidade', '1')))
                    subtotal = preco_unitario * quantidade
                    total_pedido += subtotal

                    # 1. Cria o ItemPedido sem as personalizações
                    item_pedido = ItemPedido.objects.create(
                        pedido=pedido,
                        produto=produto,
                        quantidade=item_data['quantidade'],
                        preco_unitario=preco_unitario,
                        subtotal=subtotal,
                        observacoes=item_data.get('observacoes', '')
                        # O campo 'personalizacoes' que é um JSONField foi removido, 
                        # pois o erro indica uma relação de banco de dados.
                    )

                    # 2. Itera sobre as personalizações do carrinho e cria os objetos
                    personalizacoes_data = item_data.get('personalizacoes', [])
                    if personalizacoes_data:
                        for perso_data in personalizacoes_data:
                            PersonalizacaoItemPedido.objects.create(
                                item_pedido=item_pedido,
                                nome_opcao=perso_data.get('opcao', 'N/A'),
                                nome_item=perso_data.get('nome', 'N/A'),
                                preco=Decimal(str(perso_data.get('preco', '0')))
                            )

                except (Produto.DoesNotExist, ValueError, InvalidOperation):
                    messages.error(request, f"Um produto no seu carrinho não foi encontrado ou tem dados inválidos (ID: {produto_id_key}).")
                    continue
            
            pedido.subtotal = total_pedido
            pedido.total = total_pedido + pedido.taxa_entrega
            pedido.save()

            if 'carrinho' in request.session:
                del request.session['carrinho']
                request.session.modified = True

            # Criar histórico inicial do pedido
            HistoricoStatusPedido.objects.create(
                pedido=pedido,
                status_anterior=None,
                status_novo=pedido.status,
                observacoes='Pedido criado pelo cliente.'
            )

            messages.success(request, 'Pedido realizado com sucesso!')
            request.session['ultimo_pedido_id'] = str(pedido.id) 
            return redirect('loja:confirmacao_pedido', restaurante_slug=kwargs.get('restaurante_slug'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_message = f'Ocorreu um erro inesperado ao finalizar seu pedido. Detalhe: {type(e).__name__}: {e}'
            messages.error(request, error_message)
            return redirect('loja:checkout', restaurante_slug=kwargs.get('restaurante_slug'))


class ConfirmarPedidoView(BaseLojaView):
    """Exibe a página de confirmação do pedido."""
    template_name = 'loja/confirmacao_pedido.html'

    def get(self, request, *args, **kwargs):
        ultimo_pedido_id = self.request.session.get('ultimo_pedido_id')

        if not ultimo_pedido_id:
            messages.warning(self.request, 'Não há um pedido recente para confirmar.')
            # Usar kwargs para pegar o restaurante_slug da URL
            restaurante_slug = kwargs.get('restaurante_slug')
            if restaurante_slug:
                return redirect('loja:home', restaurante_slug=restaurante_slug)
            else:
                return redirect('landing_page')

        context = self.get_context_data(**kwargs)
        
        try:
            # Buscar o pedido com todos os dados relacionados
            pedido = get_object_or_404(
                Pedido.objects.select_related('restaurante', 'cliente')
                .prefetch_related(
                    'itens__produto', 
                    'itens__personalizacoes',
                    'historico_status'
                ), 
                id=ultimo_pedido_id
            )
            context['pedido'] = pedido
            print(f"✅ Pedido carregado: {pedido.numero} - {pedido.itens.count()} itens")
        except Http404:
            messages.error(self.request, 'Pedido não encontrado.')
            context['pedido'] = None
        except Exception as e:
            messages.error(self.request, f'Ocorreu um erro ao buscar os detalhes do pedido: {e}')
            context['pedido'] = None
            import traceback
            traceback.print_exc()
            
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Este método agora só adiciona o contexto base. 
        # A lógica do pedido foi movida para o método get.
        return context


class DetalhesPedidoView(BaseLojaView):
    """Página de detalhes do pedido"""
    template_name = 'loja/detalhes_pedido.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pedido_id = kwargs.get('pedido_id')
        
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Se usuário logado, verificar se é dono do pedido
        if self.request.user.is_authenticated and pedido.cliente != self.request.user:
            # Aqui poderia adicionar uma verificação adicional por celular/email
            pass
        
        context['pedido'] = pedido
        context['itens_pedido'] = pedido.itens.all().prefetch_related('personalizacoes')
        
        return context


class AcompanharPedidoView(BaseLojaView):
    """Acompanhar pedido por número"""
    template_name = 'loja/acompanhar_pedido.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        numero_pedido = kwargs.get('numero_pedido')
        
        try:
            pedido = Pedido.objects.get(numero=numero_pedido)
            context['pedido'] = pedido
            context['historico_status'] = pedido.historico_status.all()
        except Pedido.DoesNotExist:
            context['pedido_nao_encontrado'] = True
        
        return context


class MeusPedidosView(BaseLojaView):
    """Página de pedidos do usuário - permite busca por celular ou usuário logado"""
    template_name = 'loja/meus_pedidos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        pedidos = Pedido.objects.none()
        celular_busca = None
        
        # Se usuário logado, buscar seus pedidos
        if self.request.user.is_authenticated:
            pedidos = Pedido.objects.filter(
                cliente=self.request.user,
                restaurante=context['restaurante']
            ).exclude(status='carrinho').order_by('-created_at')

        # Se foi feita busca por celular
        celular_busca = self.request.GET.get('celular', '').strip()
        if celular_busca:
            celular_limpo = ''.join(filter(str.isdigit, celular_busca))
            pedidos_celular = Pedido.objects.filter(
                cliente_celular=celular_limpo,
                restaurante=context['restaurante']
            ).exclude(status='carrinho').order_by('-created_at')
            # Se usuário logado e buscou seu próprio celular, combinar resultados
            if self.request.user.is_authenticated:
                pedidos = pedidos.union(pedidos_celular).order_by('-created_at')
            else:
                pedidos = pedidos_celular
        # Se não está logado e não buscou manualmente, não mostra nenhum pedido
        elif not self.request.user.is_authenticated:
            pedidos = Pedido.objects.none()
        
        # Paginação
        paginator = Paginator(pedidos, 10)
        page_number = self.request.GET.get('page')
        pedidos_paginated = paginator.get_page(page_number)
        
        context.update({
            'pedidos': pedidos_paginated,
            'celular_busca': celular_busca,
            'total_pedidos': pedidos.count() if pedidos else 0
        })
        
        return context


class PerfilView(LoginRequiredMixin, BaseLojaView):
    """Página de perfil do usuário"""
    template_name = 'loja/perfil.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enderecos'] = self.request.user.enderecos.all()
        return context


class SobreView(BaseLojaView):
    """Página sobre o restaurante"""
    template_name = 'loja/sobre.html'


class ContatoView(BaseLojaView):
    """Página de contato"""
    template_name = 'loja/contato.html'


class BuscarCEPView(View):
    """API para buscar dados do CEP"""
    
    def get(self, request):
        cep = request.GET.get('cep', '').replace('-', '').replace('.', '')
        
        if len(cep) != 8:
            return JsonResponse({'error': 'CEP inválido'}, status=400)
        
        try:
            # Usar API dos Correios ou ViaCEP
            response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
            data = response.json()
            
            if 'erro' in data:
                return JsonResponse({'error': 'CEP não encontrado'}, status=404)
            
            return JsonResponse({
                'logradouro': data.get('logradouro', ''),
                'bairro': data.get('bairro', ''),
                'cidade': data.get('localidade', ''),
                'estado': data.get('uf', ''),
            })
            
        except Exception as e:
            return JsonResponse({'error': 'Erro ao buscar CEP'}, status=500)


class CalcularEntregaView(View):
    """API para calcular taxa de entrega"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            cep = data.get('cep')
            
            # Por enquanto, retornar taxa fixa
            # Futuramente integrar com APIs de entrega
            restaurante = Restaurante.objects.filter(status='ativo').first()
            taxa_entrega = float(restaurante.taxa_entrega) if restaurante else 5.00
            
            return JsonResponse({
                'taxa_entrega': taxa_entrega,
                'tempo_estimado': f"{restaurante.tempo_entrega_min}-{restaurante.tempo_entrega_max} min" if restaurante else "30-60 min"
            })
            
        except Exception as e:
            return JsonResponse({'error': 'Erro ao calcular entrega'}, status=500)


class ProdutoAjaxView(BaseLojaView, View):
    """View AJAX para obter dados de um produto"""
    
    def get(self, request, produto_id):
        try:
            restaurante = Restaurante.objects.filter(status='ativo').first()
            produto = get_object_or_404(
                Produto, 
                id=produto_id, 
                restaurante=restaurante,
                disponivel=True
            )
            
            data = {
                'success': True,
                'produto': {
                    'id': produto.id,
                    'nome': produto.nome,
                    'descricao': produto.descricao,
                    'preco': float(produto.preco),
                    'preco_final': float(produto.preco_final),
                    'imagem_principal': produto.imagem_principal.url if produto.imagem_principal else None,
                    'categoria': produto.categoria.nome if produto.categoria else None,
                    'tempo_preparo': produto.tempo_preparo,
                    'calorias': produto.calorias,
                    'disponivel': produto.disponivel,
                    'tem_promocao': produto.tem_promocao,
                }
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Produto não encontrado'
            }, status=404)


class AdicionarCarrinhoAjaxView(BaseLojaView, View):
    """View AJAX para adicionar produto ao carrinho"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            quantidade = int(data.get('quantidade', 1))
            observacoes = data.get('observacoes', '')
            
            # Validar produto
            restaurante = Restaurante.objects.filter(status='ativo').first()
            produto = get_object_or_404(
                Produto, 
                id=produto_id, 
                restaurante=restaurante,
                disponivel=True
            )
            
            # Obter carrinho da sessão
            carrinho = request.session.get('carrinho', {})
            
            # Criar chave única para o item (produto + observações)
            item_key = f"{produto_id}_{hash(observacoes)}"
            
            if item_key in carrinho:
                carrinho[item_key]['quantidade'] += quantidade
            else:
                carrinho[item_key] = {
                    'produto_id': produto.id,
                    'nome': produto.nome,
                    'preco': float(produto.preco_final),
                    'quantidade': quantidade,
                    'observacoes': observacoes,
                    'imagem': produto.imagem_principal.url if produto.imagem_principal else None
                }
            
            request.session['carrinho'] = carrinho
            request.session.modified = True
            
            # Calcular totais
            total_itens = sum(item['quantidade'] for item in carrinho.values())
            total_valor = sum(item['preco'] * item['quantidade'] for item in carrinho.values())
            
            return JsonResponse({
                'success': True,
                'message': 'Produto adicionado ao carrinho!',
                'total_itens': total_itens,
                'total_valor': float(total_valor)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao adicionar produto ao carrinho'
            }, status=400)


class BuscarCEPView(View):
    """View para buscar dados do CEP via API externa"""
    
    def get(self, request):
        cep = request.GET.get('cep', '').replace('-', '').replace(' ', '')
        
        if not cep or len(cep) != 8:
            return JsonResponse({
                'error': 'CEP inválido'
            }, status=400)
        
        try:
            # Simular dados do CEP (em produção, usar API real como ViaCEP)
            dados_cep = {
                '01310100': {
                    'logradouro': 'Avenida Paulista',
                    'bairro': 'Bela Vista',
                    'cidade': 'São Paulo',
                    'estado': 'SP'
                },
                '22071900': {
                    'logradouro': 'Avenida Atlântica',
                    'bairro': 'Copacabana',
                    'cidade': 'Rio de Janeiro',
                    'estado': 'RJ'
                }
            }
            
            if cep in dados_cep:
                return JsonResponse(dados_cep[cep])
            else:
                # Em produção, fazer chamada para API externa
                return JsonResponse({
                    'logradouro': f'Rua do CEP {cep[:2]}',
                    'bairro': 'Centro',
                    'cidade': 'Cidade Exemplo',
                    'estado': 'SP'
                })
                
        except Exception as e:
            return JsonResponse({
                'error': 'Erro ao buscar CEP'
            }, status=500)


class AcessarPedidosView(BaseLojaView):
    """Página para o cliente acessar seus pedidos com o número do celular."""
    template_name = 'loja/acessar_pedidos.html'

    def get(self, request, *args, **kwargs):
        # Apenas renderiza a página com o formulário
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        celular = request.POST.get('celular', '').strip()
        context = self.get_context_data()

        if not celular:
            messages.error(request, 'Por favor, informe um número de celular.')
            return self.render_to_response(context)

        # Busca o usuário pelo celular
        usuario = Usuario.objects.filter(celular=celular).first()

        if usuario:
            # Busca os pedidos associados ao usuário no restaurante atual
            pedidos = Pedido.objects.filter(
                cliente=usuario,
                restaurante=context['restaurante']
            ).prefetch_related('historico_status', 'itens').order_by('-created_at')
            
            context['pedidos_encontrados'] = pedidos
            context['celular_buscado'] = celular
            context['usuario_encontrado'] = usuario
            
            if not pedidos.exists():
                messages.info(request, f'Nenhum pedido encontrado para o número {celular} neste restaurante.')
            else:
                messages.success(request, f'Encontrados {pedidos.count()} pedido(s) para o número {celular}.')
        else:
            messages.warning(request, 'Nenhum cliente encontrado com este número de celular.')
            
        return self.render_to_response(context)


class RemoverItemCarrinhoView(View):
    """Remover item específico do carrinho via AJAX"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            
            if not produto_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID do produto não fornecido'
                }, status=400)
            
            carrinho = request.session.get('carrinho', {})
            
            # Procurar e remover item com o produto_id
            items_removidos = 0
            for item_key in list(carrinho.keys()):
                if carrinho[item_key]['produto_id'] == str(produto_id):
                    del carrinho[item_key]
                    items_removidos += 1
            
            if items_removidos > 0:
                request.session['carrinho'] = carrinho
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'message': 'Item removido do carrinho'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Item não encontrado no carrinho'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao remover item: {str(e)}'
            }, status=500)


class AlterarQuantidadeCarrinhoView(View):
    """Alterar quantidade de item no carrinho via AJAX"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            delta = int(data.get('delta', 0))
            
            if not produto_id or delta == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Dados inválidos'
                }, status=400)
            
            carrinho = request.session.get('carrinho', {})
            
            # Procurar item no carrinho
            item_encontrado = False
            for item_key in carrinho.keys():
                if carrinho[item_key]['produto_id'] == str(produto_id):
                    nova_quantidade = carrinho[item_key]['quantidade'] + delta
                    
                    if nova_quantidade <= 0:
                        # Remover item se quantidade for 0 ou menor
                        del carrinho[item_key]
                    else:
                        carrinho[item_key]['quantidade'] = nova_quantidade
                    
                    item_encontrado = True
                    break
            
            if item_encontrado:
                request.session['carrinho'] = carrinho
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'message': 'Quantidade atualizada'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Item não encontrado no carrinho'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao alterar quantidade: {str(e)}'
            }, status=500)


class LimparCarrinhoAjaxView(View):
    """Limpar todo o carrinho via AJAX"""
    
    def post(self, request, *args, **kwargs):
        try:
            request.session['carrinho'] = {}
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'message': 'Carrinho limpo com sucesso'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao limpar carrinho: {str(e)}'
            }, status=500)
