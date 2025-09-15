from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages

# ...existing code...

# View para adicionar endereço do cliente
class AdicionarEnderecoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'loja/endereco_adicionar.html')

    def post(self, request, *args, **kwargs):
        from core.models import Endereco
        usuario = request.user
        nome = request.POST.get('nome')
        cep = request.POST.get('cep')
        logradouro = request.POST.get('logradouro')
        numero = request.POST.get('numero')
        complemento = request.POST.get('complemento')
        bairro = request.POST.get('bairro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')
        ponto_referencia = request.POST.get('ponto_referencia')
        principal = bool(request.POST.get('principal'))

        if principal:
            Endereco.objects.filter(usuario=usuario, principal=True).update(principal=False)

        Endereco.objects.create(
            usuario=usuario,
            nome=nome,
            cep=cep,
            logradouro=logradouro,
            numero=numero,
            complemento=complemento,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            ponto_referencia=ponto_referencia,
            principal=principal
        )
        messages.success(request, 'Endereço adicionado com sucesso!')
        return redirect(reverse('loja:perfil', kwargs={'restaurante_slug': kwargs.get('restaurante_slug')}))

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin

# --- Autenticação do Cliente ---
class LoginClienteView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('loja:home', restaurante_slug=kwargs.get('restaurante_slug'))
        restaurante_slug = kwargs.get('restaurante_slug')
        restaurante = None
        if restaurante_slug:
            from core.models import Restaurante
            try:
                restaurante = Restaurante.objects.get(slug=restaurante_slug)
            except Restaurante.DoesNotExist:
                restaurante = None
        return render(request, 'loja/login.html', {'restaurante': restaurante})

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        restaurante_slug = kwargs.get('restaurante_slug')
        restaurante = None
        if restaurante_slug:
            from core.models import Restaurante
            try:
                restaurante = Restaurante.objects.get(slug=restaurante_slug)
            except Restaurante.DoesNotExist:
                restaurante = None
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('loja:home', restaurante_slug=restaurante_slug)
        messages.error(request, 'Usuário ou senha inválidos.')
        return render(request, 'loja/login.html', {'username': username, 'restaurante': restaurante})

class LogoutClienteView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('loja:login', restaurante_slug=kwargs.get('restaurante_slug'))

class CadastroClienteView(View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('loja:home', restaurante_slug=kwargs.get('restaurante_slug'))
        restaurante_slug = kwargs.get('restaurante_slug')
        restaurante = None
        if restaurante_slug:
            from core.models import Restaurante
            try:
                restaurante = Restaurante.objects.get(slug=restaurante_slug)
            except Restaurante.DoesNotExist:
                restaurante = None
        return render(request, 'loja/cadastro.html', {'restaurante': restaurante})

    def post(self, request, *args, **kwargs):
        User = get_user_model()
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        celular = request.POST.get('celular')
        password = request.POST.get('password1')
        password2 = request.POST.get('password2')
        restaurante_slug = kwargs.get('restaurante_slug')
        restaurante = None
        if restaurante_slug:
            from core.models import Restaurante
            try:
                restaurante = Restaurante.objects.get(slug=restaurante_slug)
            except Restaurante.DoesNotExist:
                restaurante = None

        if password != password2:
            from django.contrib import messages
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'loja/cadastro.html', {**request.POST, 'restaurante': restaurante})

        if User.objects.filter(email=email).exists():
            from django.contrib import messages
            messages.error(request, 'Já existe uma conta com este e-mail.')
            return render(request, 'loja/cadastro.html', {**request.POST, 'restaurante': restaurante})

        if User.objects.filter(celular=celular).exists():
            from django.contrib import messages
            messages.error(request, 'Já existe uma conta com este celular.')
            return render(request, 'loja/cadastro.html', {**request.POST, 'restaurante': restaurante})

        user = User.objects.create_user(username=email, email=email, first_name=nome, celular=celular)
        user.set_password(password)
        user.save()
        # Vincular cliente ao restaurante
        if restaurante:
            from core.models import RestauranteCliente
            RestauranteCliente.objects.get_or_create(restaurante=restaurante, cliente=user)
        login(request, user)
        return redirect('loja:home', restaurante_slug=restaurante_slug)
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.db import models, transaction
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
    PersonalizacaoItemPedido, ItemPersonalizacao, OpcaoPersonalizacao, Usuario, Endereco, HistoricoStatusPedido
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
            print(f"HomeView: {len(produtos_populares)} produtos populares, dados JS preparados")
        
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
    """Busca de produtos com filtros avançados"""
    template_name = 'loja/buscar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        categoria_filter = self.request.GET.get('categoria', '')
        
        produtos = []
        categorias_com_resultados = []
        sugestoes = []
        
        if context['restaurante'] and query:
            # Busca principal
            produtos_query = context['restaurante'].produtos.filter(
                disponivel=True
            ).select_related('categoria')
            
            # Aplicar filtro de categoria se especificado
            if categoria_filter:
                produtos_query = produtos_query.filter(categoria__slug=categoria_filter)
            
            # Busca por relevância (nome tem prioridade)
            produtos_nome = produtos_query.filter(
                Q(nome__icontains=query)
            ).order_by('nome')
            
            # Busca em descrição
            produtos_descricao = produtos_query.filter(
                Q(descricao__icontains=query)
            ).exclude(
                id__in=produtos_nome.values_list('id', flat=True)
            ).order_by('nome')
            
            # Busca em categoria
            produtos_categoria = produtos_query.filter(
                Q(categoria__nome__icontains=query)
            ).exclude(
                id__in=produtos_nome.values_list('id', flat=True)
            ).exclude(
                id__in=produtos_descricao.values_list('id', flat=True)
            ).order_by('nome')
            
            # Combinar resultados por relevância
            produtos_list = list(produtos_nome) + list(produtos_descricao) + list(produtos_categoria)
            
            # Paginação
            paginator = Paginator(produtos_list, 12)
            page_number = self.request.GET.get('page')
            produtos = paginator.get_page(page_number)
            
            # Categorias que têm produtos nos resultados
            if produtos_list:
                categorias_com_resultados = context['restaurante'].categorias.filter(
                    produtos__in=[p.id for p in produtos_list]
                ).distinct().order_by('nome')
            
            # Sugestões se não houver resultados ou poucos resultados
            if len(produtos_list) < 3:
                # Buscar produtos similares
                palavras = query.split()
                if palavras:
                    sugestoes_query = context['restaurante'].produtos.filter(
                        disponivel=True
                    )
                    
                    for palavra in palavras:
                        if len(palavra) > 2:  # Ignorar palavras muito pequenas
                            sugestoes_query = sugestoes_query.filter(
                                Q(nome__icontains=palavra) |
                                Q(descricao__icontains=palavra) |
                                Q(categoria__nome__icontains=palavra)
                            )
                    
                    # Excluir produtos já nos resultados
                    if produtos_list:
                        sugestoes_query = sugestoes_query.exclude(
                            id__in=[p.id for p in produtos_list]
                        )
                    
                    sugestoes = list(sugestoes_query.order_by('nome')[:6])
            
            context.update({
                'produtos': produtos,
                'query': query,
                'categoria_filter': categoria_filter,
                'total_resultados': len(produtos_list),
                'categorias_com_resultados': categorias_com_resultados,
                'sugestoes': sugestoes,
                'tem_resultados': len(produtos_list) > 0,
            })
        else:
            # Se não há query, mostrar categorias disponíveis
            if context['restaurante']:
                context['todas_categorias'] = context['restaurante'].categorias.filter(
                    produtos__disponivel=True
                ).distinct().order_by('nome')
            
            context.update({
                'produtos': produtos,
                'query': query,
                'total_resultados': 0,
                'tem_resultados': False,
            })
        
        return context


class CarrinhoViewOriginal(BaseLojaView):
    """Página do carrinho"""
    template_name = 'loja/carrinho.html'
    
    def get(self, request, *args, **kwargs):
        # Se for requisição AJAX, retornar JSON
        if request.headers.get('Accept') == 'application/json':
            carrinho = request.session.get('carrinho', {})
            print(f"DEBUG CarrinhoView: Carrinho da sessão = {carrinho}")
            carrinho_count = sum(item['quantidade'] for item in carrinho.values())
            print(f"DEBUG CarrinhoView: Carrinho count = {carrinho_count}")
            
            # Buscar detalhes dos produtos e preparar lista de itens
            itens_carrinho = []
            total_valor = 0
            
            for item_key, item in carrinho.items():
                try:
                    produto_id = item['produto_id']
                    meio_a_meio = item.get('meio_a_meio')
                    
                    # Para pizzas meio-a-meio, usar dados salvos na sessão
                    if meio_a_meio:
                        produto_nome = item.get('nome', 'Pizza Meio-a-Meio')
                        categoria_nome = item.get('categoria', 'Pizzas')
                        imagem_url = item.get('imagem')
                    else:
                        produto = Produto.objects.get(id=produto_id)
                        produto_nome = produto.nome
                        categoria_nome = produto.categoria.nome if produto.categoria else ''
                        imagem_url = produto.imagem_principal.url if produto.imagem_principal else None
                    
                    subtotal = item['preco'] * item['quantidade']
                    total_valor += subtotal
                    
                    itens_carrinho.append({
                        'produto_id': produto_id,
                        'nome': produto_nome,
                        'categoria': categoria_nome,
                        'quantidade': item['quantidade'],
                        'preco_unitario': item['preco'],
                        'preco_total': subtotal,
                        'personalizacoes': item.get('personalizacoes', []),
                        'observacoes': item.get('observacoes', ''),
                        'item_key': item_key,
                        # Adicionar campos que o frontend precisa
                        'preco': item['preco'],  # Compatibilidade
                        'imagem': imagem_url,
                        'meio_a_meio': meio_a_meio,
                    })
                except Produto.DoesNotExist:
                    continue
            
            # Dados do restaurante - CORRIGIDO
            restaurante_data = None
            restaurante_slug = kwargs.get('restaurante_slug') or self.request.resolver_match.kwargs.get('restaurante_slug')
            
            if restaurante_slug:
                try:
                    restaurante = Restaurante.objects.get(slug=restaurante_slug, status='ativo')
                    endereco_completo = f"{restaurante.logradouro}, {restaurante.numero}"
                    if restaurante.complemento:
                        endereco_completo += f", {restaurante.complemento}"
                    endereco_completo += f" - {restaurante.bairro}, {restaurante.cidade}/{restaurante.estado}"
                    
                    restaurante_data = {
                        'nome': restaurante.nome,
                        'endereco': endereco_completo,
                        'slug': restaurante.slug
                    }
                    print(f"DEBUG CarrinhoView: Restaurante encontrado = {restaurante.nome}")
                except Restaurante.DoesNotExist:
                    print(f"DEBUG CarrinhoView: Restaurante {restaurante_slug} não encontrado")
            else:
                print("DEBUG CarrinhoView: Slug do restaurante não encontrado")
            
            response_data = {
                'carrinho_count': carrinho_count,
                'total_items': len(carrinho),
                'items': itens_carrinho,
                'total': total_valor,
                'restaurante': restaurante_data
            }
            print(f"DEBUG CarrinhoView: Resposta = {response_data}")
            
            return JsonResponse(response_data)
        
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
                meio_a_meio = item.get('meio_a_meio')
                
                # Para pizzas meio-a-meio, usar dados salvos na sessão
                if meio_a_meio:
                    produto_nome = item.get('nome', 'Pizza Meio-a-Meio')
                    categoria_nome = item.get('categoria', 'Pizzas')
                    imagem_url = item.get('imagem')
                    
                    # Criar objeto mock para compatibilidade com o template
                    class ProdutoMock:
                        def __init__(self, nome, categoria_nome, imagem_url):
                            self.nome = nome
                            self.categoria = type('obj', (object,), {'nome': categoria_nome})() if categoria_nome else None
                            self.imagem_principal = type('obj', (object,), {'url': imagem_url})() if imagem_url else None
                    
                    produto = ProdutoMock(produto_nome, categoria_nome, imagem_url)
                else:
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
                    'meio_a_meio': meio_a_meio,
                })
            except Produto.DoesNotExist:
                continue
        
        context['itens_carrinho'] = itens_carrinho
        context['total_carrinho'] = total
        context['carrinho_count'] = sum(item['quantidade'] for item in carrinho.values())
        
        return context


class AdicionarCarrinhoView(View):
    """Adicionar produto ao carrinho via AJAX - Nova arquitetura"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            quantidade = int(data.get('quantidade', 1))
            personalizacoes_data = data.get('personalizacoes', [])
            observacoes = data.get('observacoes', '')
            
            # Validações básicas
            if not produto_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID do produto é obrigatório'
                }, status=400)
            
            # Verificar se é pizza meio-a-meio (ID customizado)
            meio_a_meio_data = data.get('meio_a_meio')
            nome_customizado = data.get('nome')
            preco_customizado = data.get('preco_unitario')
            is_meio_a_meio = str(produto_id).startswith('meio-') or meio_a_meio_data is not None
            
            # Obter restaurante
            restaurante_slug = kwargs.get('restaurante_slug')
            if not restaurante_slug:
                return JsonResponse({
                    'success': False,
                    'error': 'Restaurante não identificado'
                }, status=400)
            
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            
            # Para pizzas meio-a-meio, usar produto base de pizza
            if is_meio_a_meio:
                # Se temos dados de meio-a-meio, usar o primeiro sabor como produto base
                if meio_a_meio_data and isinstance(meio_a_meio_data, dict):
                    primeiro_sabor = meio_a_meio_data.get('primeiro_sabor', {})
                    primeiro_sabor_id = primeiro_sabor.get('id')
                    if primeiro_sabor_id:
                        try:
                            produto = Produto.objects.get(id=primeiro_sabor_id, restaurante=restaurante, disponivel=True)
                        except Produto.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Primeiro sabor não encontrado'
                            }, status=400)
                    else:
                        # Fallback: buscar primeiro produto de pizza disponível
                        produto = Produto.objects.filter(
                            restaurante=restaurante, 
                            categoria__nome__icontains='pizza',
                            disponivel=True
                        ).first()
                else:
                    # Fallback: buscar primeiro produto de pizza disponível
                    produto = Produto.objects.filter(
                        restaurante=restaurante, 
                        categoria__nome__icontains='pizza',
                        disponivel=True
                    ).first()
                
                if not produto:
                    return JsonResponse({
                        'success': False,
                        'error': 'Produto base para pizza não encontrado'
                    }, status=400)
            else:
                produto = get_object_or_404(Produto, id=produto_id, restaurante=restaurante, disponivel=True)
            
            # Obter carrinho usando Service Layer
            # Garantir que existe sessão_id
            if not request.session.session_key:
                request.session.create()
                
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            # Processar personalizações se existirem
            personalizacoes = []
            if personalizacoes_data:
                for p in personalizacoes_data:
                    try:
                        # Buscar a personalização/opção
                        if p.get('opcao_id'):
                            opcao = OpcaoPersonalizacao.objects.get(id=p['opcao_id'])
                            personalizacoes.append({
                                'opcao_id': p['opcao_id'],
                                'item_id': p.get('item_id'),
                                'nome': p.get('nome', opcao.nome),
                                'preco_adicional': float(p.get('preco_adicional', p.get('preco', 0)))
                            })
                    except OpcaoPersonalizacao.DoesNotExist:
                        continue
            
            # Preparar dados adicionais para meio-a-meio
            dados_meio_a_meio = None
            if is_meio_a_meio:
                dados_meio_a_meio = {
                    'nome_customizado': nome_customizado,
                    'preco_customizado': float(preco_customizado) if preco_customizado else None,
                    'dados_originais': meio_a_meio_data,
                    'produto_id_original': produto_id  # Manter o ID original meio-uuid-uuid
                }
            
            # Adicionar item ao carrinho usando Service Layer
            item = CarrinhoService.adicionar_item(
                carrinho=carrinho,
                produto=produto,
                quantidade=quantidade,
                personalizacoes=personalizacoes,
                observacoes=observacoes,
                dados_meio_a_meio=dados_meio_a_meio
            )
            
            # Calcular resumo atualizado
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            return JsonResponse({
                'success': True,
                'message': 'Produto adicionado ao carrinho!',
                'carrinho_count': resumo['total_itens'],
                'total_carrinho': float(resumo['subtotal'])
            })
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao adicionar produto: {str(e)}'
            }, status=500)


class RemoverCarrinhoView(View):
    """Remover item do carrinho - Nova arquitetura"""
    
    def post(self, request, restaurante_slug, item_id):
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            
            # Obter carrinho
            # Garantir que existe sessão_id
            if not request.session.session_key:
                request.session.create()
                
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            # Remover item
            CarrinhoService.remover_item(carrinho, item_id)
            messages.success(request, 'Item removido do carrinho!')
            
        except Exception as e:
            messages.error(request, f'Erro ao remover item: {str(e)}')
        
        return redirect('loja:carrinho', restaurante_slug=restaurante_slug)


class LimparCarrinhoView(View):
    """Limpar todo o carrinho - Nova arquitetura"""
    
    def post(self, request, restaurante_slug):
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            # Limpar carrinho
            CarrinhoService.limpar_carrinho(carrinho)
            messages.success(request, 'Carrinho limpo!')
            
        except Exception as e:
            messages.error(request, f'Erro ao limpar carrinho: {str(e)}')
        
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
                
                meio_a_meio = item.get('meio_a_meio')
                
                # Para pizzas meio-a-meio, usar dados salvos na sessão
                if meio_a_meio:
                    produto_nome = item.get('nome', 'Pizza Meio-a-Meio')
                    categoria_nome = item.get('categoria', 'Pizzas')
                    imagem_url = item.get('imagem')
                    
                    # Criar objeto mock para compatibilidade com o template
                    class ProdutoMock:
                        def __init__(self, nome, categoria_nome, imagem_url):
                            self.nome = nome
                            self.categoria = type('obj', (object,), {'nome': categoria_nome})() if categoria_nome else None
                            self.imagem_principal = type('obj', (object,), {'url': imagem_url})() if imagem_url else None
                    
                    produto = ProdutoMock(produto_nome, categoria_nome, imagem_url)
                else:
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
                    'meio_a_meio': meio_a_meio,
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
        print(f"🛒 Headers: {dict(request.headers)}")
        print(f"🛒 Body: {request.body[:500]}...")  # Primeiros 500 chars
        
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
                    try:
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
                    except Exception as e:
                        from django.db import IntegrityError
                        if isinstance(e, IntegrityError) and 'celular' in str(e):
                            mensagem_erro = 'Já existe uma conta cadastrada com este número de celular. Faça login ou utilize outro número.'
                            return render(request, 'loja/checkout.html', {'erro_cadastro': mensagem_erro})
                        else:
                            raise

            pedido = Pedido.objects.create(
                restaurante=restaurante,
                cliente=cliente_instance,
                cliente_nome=data.get('nome'),
                cliente_celular=cliente_celular,
                cliente_email=data.get('email', ''),
                tipo_entrega=tipo_entrega,
                forma_pagamento=data.get('forma_pagamento'),
                observacoes=data.get('observacoes', ''),
                taxa_entrega=0,  # será calculada abaixo
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

                # Salvar endereço para o cliente logado, se não existir igual
                if cliente_instance and cliente_instance.is_authenticated:
                    from core.models import Endereco
                    endereco_existente = Endereco.objects.filter(
                        usuario=cliente_instance,
                        cep=pedido.endereco_cep,
                        logradouro=pedido.endereco_logradouro,
                        numero=pedido.endereco_numero
                    ).first()
                    if not endereco_existente:
                        # Tornar todos os outros endereços não principais
                        Endereco.objects.filter(usuario=cliente_instance, principal=True).update(principal=False)
                        Endereco.objects.create(
                            usuario=cliente_instance,
                            nome='Principal',
                            cep=pedido.endereco_cep,
                            logradouro=pedido.endereco_logradouro,
                            numero=pedido.endereco_numero,
                            complemento=pedido.endereco_complemento,
                            bairro=pedido.endereco_bairro,
                            cidade=pedido.endereco_cidade,
                            estado=pedido.endereco_estado,
                            ponto_referencia=pedido.endereco_ponto_referencia,
                            principal=True
                        )

                # Calcular frete automaticamente após salvar endereço
                pedido.taxa_entrega = pedido.calcular_frete()
                pedido.save(update_fields=["taxa_entrega"])

            total_pedido = Decimal('0.0')
            for produto_id_key, item_data in carrinho.items():
                try:
                    # Extrair o UUID do produto da chave (formato: uuid_hash)
                    if '_' in produto_id_key:
                        produto_id = produto_id_key.split('_')[0]
                    else:
                        produto_id = produto_id_key
                    
                    meio_a_meio = item_data.get('meio_a_meio')
                    print(f"🔍 DEBUG: produto_id_key={produto_id_key}, produto_id={produto_id}, meio_a_meio={bool(meio_a_meio)}")
                    
                    # Para pizzas meio-a-meio, usar o primeiro sabor como produto base
                    if meio_a_meio and isinstance(meio_a_meio, dict):
                        primeiro_sabor = meio_a_meio.get('primeiro_sabor', {})
                        produto_id_real = primeiro_sabor.get('id')
                        if produto_id_real:
                            produto = Produto.objects.get(id=produto_id_real)
                        else:
                            print(f"❌ Erro: ID do primeiro sabor não encontrado em meio_a_meio")
                            continue
                    else:
                        produto = Produto.objects.get(id=produto_id)
                    
                    # Garantir que os cálculos são feitos com Decimal
                    preco_unitario = Decimal(str(item_data.get('preco', '0')))
                    quantidade = Decimal(str(item_data.get('quantidade', '1')))
                    subtotal = preco_unitario * quantidade
                    total_pedido += subtotal

                    # Definir nome do produto para pizzas meio-a-meio
                    produto_nome_customizado = item_data.get('nome')
                    if meio_a_meio and produto_nome_customizado:
                        produto_nome_final = produto_nome_customizado
                    else:
                        produto_nome_final = produto.nome
                    
                    # 1. Cria o ItemPedido sem as personalizações
                    item_pedido = ItemPedido.objects.create(
                        pedido=pedido,
                        produto=produto,
                        produto_nome=produto_nome_final,
                        quantidade=item_data['quantidade'],
                        preco_unitario=preco_unitario,
                        subtotal=subtotal,
                        observacoes=item_data.get('observacoes', ''),
                        meio_a_meio=item_data.get('meio_a_meio')
                    )

                    # 2. Itera sobre as personalizações do carrinho e cria os objetos
                    personalizacoes_data = item_data.get('personalizacoes', [])
                    if personalizacoes_data:
                        for perso_data in personalizacoes_data:
                            try:
                                # Buscar o ItemPersonalizacao pelo ID
                                item_personalizacao = ItemPersonalizacao.objects.get(
                                    id=perso_data.get('item_id')
                                )
                                
                                PersonalizacaoItemPedido.objects.create(
                                    item_pedido=item_pedido,
                                    item_personalizacao=item_personalizacao,
                                    opcao_nome=perso_data.get('nome', 'N/A'),
                                    item_nome=perso_data.get('nome', 'N/A'),
                                    preco_adicional=Decimal(str(perso_data.get('preco_adicional', '0')))
                                )
                            except ItemPersonalizacao.DoesNotExist:
                                # Se o item não existir, pular esta personalização
                                print(f"ItemPersonalizacao not found for ID: {perso_data.get('item_id')}")
                                continue

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
    """Remover item específico do carrinho via AJAX - Nova arquitetura"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id') or data.get('produto_id')
            
            if not item_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID do item não fornecido'
                }, status=400)
            
            # Obter restaurante do slug (assumindo que está na URL ou session)
            restaurante_slug = kwargs.get('restaurante_slug')
            if not restaurante_slug:
                # Tentar obter da sessão ou request
                restaurante_slug = request.session.get('restaurante_slug')
            
            if restaurante_slug:
                restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
                
                # Obter carrinho
                carrinho = CarrinhoService.obter_carrinho(
                    usuario=request.user if request.user.is_authenticated else None,
                    sessao_id=request.session.session_key,
                    restaurante=restaurante
                )
                
                # Remover item
                CarrinhoService.remover_item(carrinho, item_id)
                
                # Calcular resumo atualizado
                resumo = CarrinhoService.calcular_resumo(carrinho)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Item removido do carrinho',
                    'carrinho_count': resumo['total_itens'],
                    'total_carrinho': float(resumo['subtotal'])
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Restaurante não identificado'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao remover item: {str(e)}'
            }, status=500)


class AlterarQuantidadeCarrinhoView(View):
    """Alterar quantidade de item no carrinho via AJAX - Nova arquitetura"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id') or data.get('produto_id')
            nova_quantidade = data.get('quantidade')
            delta = data.get('delta')
            
            if not item_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID do item não fornecido'
                }, status=400)
            
            # Obter restaurante do slug
            restaurante_slug = kwargs.get('restaurante_slug')
            if not restaurante_slug:
                restaurante_slug = request.session.get('restaurante_slug')
            
            if restaurante_slug:
                restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
                
                # Obter carrinho
                carrinho = CarrinhoService.obter_carrinho(
                    usuario=request.user if request.user.is_authenticated else None,
                    sessao_id=request.session.session_key,
                    restaurante=restaurante
                )
                
                # Atualizar quantidade
                if nova_quantidade is not None:
                    CarrinhoService.atualizar_quantidade(carrinho, item_id, int(nova_quantidade))
                elif delta is not None:
                    CarrinhoService.alterar_quantidade(carrinho, item_id, int(delta))
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Quantidade ou delta não fornecidos'
                    }, status=400)
                
                # Calcular resumo atualizado
                resumo = CarrinhoService.calcular_resumo(carrinho)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Quantidade atualizada',
                    'carrinho_count': resumo['total_itens'],
                    'total_carrinho': float(resumo['subtotal'])
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Restaurante não identificado'
                }, status=400)
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao alterar quantidade: {str(e)}'
            }, status=500)


class LimparCarrinhoAjaxView(View):
    """Limpar todo o carrinho via AJAX - Nova arquitetura"""
    
    def post(self, request, *args, **kwargs):
        try:
            # Obter restaurante do slug
            restaurante_slug = kwargs.get('restaurante_slug')
            if not restaurante_slug:
                restaurante_slug = request.session.get('restaurante_slug')
            
            if restaurante_slug:
                restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
                
                # Obter carrinho
                carrinho = CarrinhoService.obter_carrinho(
                    usuario=request.user if request.user.is_authenticated else None,
                    sessao_id=request.session.session_key,
                    restaurante=restaurante
                )
                
                # Limpar carrinho
                CarrinhoService.limpar_carrinho(carrinho)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Carrinho limpo com sucesso',
                    'carrinho_count': 0,
                    'total_carrinho': 0.0
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Restaurante não identificado'
                }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao limpar carrinho: {str(e)}'
            }, status=500)


# ====================== NOVA ARQUITETURA - VIEWS REFATORADAS ======================

from core.services import CarrinhoService, PedidoService, FreteService
from core.serializers import AdicionarItemCarrinhoSerializer, CriarPedidoSerializer
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class CarrinhoView(BaseLojaView):
    """Versão refatorada da view do carrinho usando CarrinhoService"""
    template_name = 'loja/carrinho.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obter carrinho usando service
            # Garantir que existe sessão_id
            if not self.request.session.session_key:
                self.request.session.create()
                
            carrinho = CarrinhoService.obter_carrinho(
                usuario=self.request.user if self.request.user.is_authenticated else None,
                sessao_id=self.request.session.session_key,
                restaurante=context['restaurante']
            )
            
            # Calcular resumo do carrinho
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            # Calcular frete se houver endereço
            taxa_entrega = 0
            if not resumo['carrinho_vazio'] and self.request.session.get('endereco_entrega'):
                taxa_entrega = FreteService.calcular_frete(
                    context['restaurante'], 
                    self.request.session.get('endereco_entrega', {}).get('cep', '')
                )
            
            context.update({
                'carrinho': carrinho,
                'itens_carrinho': resumo['itens'],
                'total_carrinho': resumo['subtotal'],
                'taxa_entrega': taxa_entrega,
                'total_final': resumo['subtotal'] + taxa_entrega,
                'carrinho_count': resumo['total_itens'],
                'total_items': len(resumo['itens']),
            })
            
            logger.info(f"Carrinho carregado: {resumo['total_itens']} itens")
            
        except Exception as e:
            logger.error(f"Erro ao carregar carrinho: {e}")
            messages.error(self.request, 'Erro ao carregar carrinho')
            context.update({
                'itens_carrinho': [],
                'total_carrinho': 0,
                'carrinho_count': 0,
                'total_items': 0,
            })
        
        return context
    
    def get(self, request, *args, **kwargs):
        # Se for requisição AJAX, retornar JSON
        if request.headers.get('Accept') == 'application/json':
            try:
                restaurante_slug = kwargs.get('restaurante_slug')
                restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
                
                # Garantir que existe sessão_id
                if not request.session.session_key:
                    request.session.create()
                
                carrinho = CarrinhoService.obter_carrinho(
                    usuario=request.user if request.user.is_authenticated else None,
                    sessao_id=request.session.session_key,
                    restaurante=restaurante
                )
                
                resumo = CarrinhoService.calcular_resumo(carrinho)
                
                # Converter Decimals para float para compatibilidade com JavaScript
                items_formatados = []
                for item in resumo['itens']:
                    item_formatado = item.copy()
                    item_formatado['preco_unitario'] = float(item['preco_unitario'])
                    item_formatado['subtotal'] = float(item['subtotal'])
                    items_formatados.append(item_formatado)
                
                return JsonResponse({
                    'success': True,
                    'carrinho_count': resumo['total_itens'],
                    'total_valor': float(resumo['subtotal']),
                    'items': items_formatados
                })
                
            except Exception as e:
                logger.error(f"Erro ao obter carrinho via AJAX: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao carregar carrinho'
                }, status=500)
        
        # Requisição normal - renderizar template
        return super().get(request, *args, **kwargs)


class AdicionarProdutoCarrinhoView(View):
    """Versão refatorada para adicionar produtos ao carrinho"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            
            # Validar dados usando serializer
            serializer = AdicionarItemCarrinhoSerializer(data=data)
            if not serializer.is_valid():
                return JsonResponse({
                    'success': False,
                    'error': 'Dados inválidos',
                    'details': serializer.errors
                }, status=400)
            
            # Obter restaurante
            restaurante_slug = kwargs.get('restaurante_slug')
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            # Obter produto
            produto_id = serializer.validated_data['produto_id']
            meio_a_meio_data = serializer.validated_data.get('meio_a_meio')
            is_meio_a_meio = str(produto_id).startswith('meio-') or meio_a_meio_data is not None
            
            if is_meio_a_meio:
                # Para meio-a-meio, usar o primeiro sabor como produto base
                if meio_a_meio_data and isinstance(meio_a_meio_data, dict):
                    primeiro_sabor = meio_a_meio_data.get('primeiro_sabor', {})
                    primeiro_sabor_id = primeiro_sabor.get('id')
                    if primeiro_sabor_id:
                        try:
                            produto = Produto.objects.get(id=primeiro_sabor_id, restaurante=restaurante, disponivel=True)
                        except Produto.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Primeiro sabor não encontrado'
                            }, status=400)
                    else:
                        # Fallback: buscar primeiro produto de pizza disponível
                        produto = Produto.objects.filter(
                            restaurante=restaurante, 
                            categoria__nome__icontains='pizza',
                            disponivel=True
                        ).first()
                else:
                    # Fallback: buscar primeiro produto de pizza disponível
                    produto = Produto.objects.filter(
                        restaurante=restaurante, 
                        categoria__nome__icontains='pizza',
                        disponivel=True
                    ).first()
                
                if not produto:
                    return JsonResponse({
                        'success': False,
                        'error': 'Produto base para pizza não encontrado'
                    }, status=400)
            else:
                produto = get_object_or_404(Produto, id=produto_id, restaurante=restaurante, disponivel=True)
            
            # Obter carrinho
            # Garantir que existe sessão_id
            if not request.session.session_key:
                request.session.create()
                
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            # Preparar dados adicionais para meio-a-meio
            dados_meio_a_meio = None
            if is_meio_a_meio:
                dados_meio_a_meio = {
                    'nome_customizado': serializer.validated_data.get('nome'),
                    'preco_customizado': float(serializer.validated_data.get('preco_unitario', 0)) if serializer.validated_data.get('preco_unitario') else None,
                    'dados_originais': meio_a_meio_data,
                    'produto_id_original': produto_id
                }
            
            # Adicionar item
            item = CarrinhoService.adicionar_item(
                carrinho=carrinho,
                produto=produto,
                quantidade=serializer.validated_data['quantidade'],
                observacoes=serializer.validated_data.get('observacoes', ''),
                personalizacoes=serializer.validated_data.get('personalizacoes', []),
                dados_meio_a_meio=dados_meio_a_meio
            )
            
            # Retornar resumo atualizado
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            return JsonResponse({
                'success': True,
                'message': 'Produto adicionado ao carrinho!',
                'carrinho_count': resumo['total_itens'],
                'total_valor': float(resumo['subtotal'])
            })
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Erro ao adicionar produto ao carrinho: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro ao adicionar produto: {str(e)}'
            }, status=500)


class CheckoutView(BaseLojaView):
    """Versão refatorada da view do checkout"""
    template_name = 'loja/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=self.request.user if self.request.user.is_authenticated else None,
                sessao_id=self.request.session.session_key,
                restaurante=context['restaurante']
            )
            
            if carrinho.esta_vazio():
                messages.warning(self.request, 'Seu carrinho está vazio')
                return context
            
            # Calcular resumo
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            # Taxa de entrega (será calculada dinamicamente no frontend)
            taxa_entrega = 0
            
            context.update({
                'carrinho': carrinho,
                'itens_carrinho': resumo['itens'],
                'total_carrinho': resumo['subtotal'],
                'taxa_entrega': taxa_entrega,
                'total_final': resumo['subtotal'] + taxa_entrega,
                'carrinho_count': resumo['total_itens'],
            })
            
            # Endereços do usuário se logado
            if self.request.user.is_authenticated:
                context['enderecos_usuario'] = self.request.user.enderecos.all()
            
            # Formas de pagamento
            context['formas_pagamento'] = [
                ('dinheiro', 'Dinheiro'),
                ('cartao_credito', 'Cartão de Crédito'),
                ('cartao_debito', 'Cartão de Débito'),
                ('pix', 'PIX'),
            ]
            
        except Exception as e:
            logger.error(f"Erro no checkout: {e}")
            messages.error(self.request, 'Erro ao carregar checkout')
            return redirect('loja:carrinho', restaurante_slug=kwargs.get('restaurante_slug'))
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Processa o pedido usando PedidoService"""
        try:
            # Obter restaurante
            restaurante_slug = kwargs.get('restaurante_slug')
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            if carrinho.esta_vazio():
                messages.error(request, 'Seu carrinho está vazio')
                return redirect('loja:carrinho', restaurante_slug=restaurante_slug)
            
            # Preparar dados do pedido
            dados_cliente = {
                'nome': request.POST.get('nome', '').strip(),
                'celular': request.POST.get('celular', '').strip(),
                'email': request.POST.get('email', '').strip(),
            }
            
            dados_entrega = {
                'tipo': request.POST.get('tipo_entrega', 'delivery'),
            }
            
            # Dados de endereço se delivery
            if dados_entrega['tipo'] == 'delivery':
                dados_entrega.update({
                    'cep': request.POST.get('cep', '').strip(),
                    'logradouro': request.POST.get('logradouro', '').strip(),
                    'numero': request.POST.get('numero', '').strip(),
                    'complemento': request.POST.get('complemento', '').strip(),
                    'bairro': request.POST.get('bairro', '').strip(),
                    'cidade': request.POST.get('cidade', '').strip(),
                    'estado': request.POST.get('estado', '').strip(),
                    'ponto_referencia': request.POST.get('ponto_referencia', '').strip(),
                })
            
            forma_pagamento = request.POST.get('forma_pagamento')
            observacoes = request.POST.get('observacoes', '').strip()
            
            # Troco se pagamento em dinheiro
            troco_para = None
            if forma_pagamento == 'dinheiro':
                troco_str = request.POST.get('troco_para', '0').replace(',', '.')
                if troco_str:
                    try:
                        from decimal import Decimal
                        troco_para = Decimal(troco_str)
                    except:
                        messages.error(request, 'Valor de troco inválido')
                        return self.get(request, *args, **kwargs)
            
            # Criar pedido usando service
            with transaction.atomic():
                pedido = PedidoService.criar_pedido_do_carrinho(
                    carrinho=carrinho,
                    dados_cliente=dados_cliente,
                    dados_entrega=dados_entrega,
                    forma_pagamento=forma_pagamento,
                    observacoes=observacoes,
                    troco_para=troco_para
                )
            
            # Salvar ID do pedido na sessão para confirmação
            request.session['ultimo_pedido_id'] = str(pedido.id)
            
            messages.success(request, f'Pedido #{pedido.numero} criado com sucesso!')
            return redirect('loja:confirmacao_pedido', restaurante_slug=restaurante_slug)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return self.get(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Erro ao processar pedido: {e}")
            messages.error(request, 'Erro interno. Tente novamente.')
            return self.get(request, *args, **kwargs)


class LimparCarrinhoView(View):
    """Versão refatorada para limpar carrinho"""
    
    def post(self, request, *args, **kwargs):
        try:
            restaurante_slug = kwargs.get('restaurante_slug')
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            CarrinhoService.limpar_carrinho(carrinho)
            
            return JsonResponse({
                'success': True,
                'message': 'Carrinho limpo com sucesso'
            })
            
        except Exception as e:
            logger.error(f"Erro ao limpar carrinho: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Erro ao limpar carrinho: {str(e)}'
            }, status=500)


import logging
logger = logging.getLogger(__name__)


class BuscarSugestoesView(BaseLojaView):
    """API para sugestões de busca em tempo real"""
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        query = request.GET.get('q', '').strip()
        
        sugestoes = []
        
        if context['restaurante'] and query and len(query) >= 2:
            # Buscar produtos que começam com a query
            produtos_nomes = list(
                context['restaurante'].produtos.filter(
                    nome__istartswith=query,
                    disponivel=True
                ).values_list('nome', flat=True)[:5]
            )
            
            # Buscar produtos que contêm a query
            produtos_contem = list(
                context['restaurante'].produtos.filter(
                    nome__icontains=query,
                    disponivel=True
                ).exclude(
                    nome__istartswith=query
                ).values_list('nome', flat=True)[:3]
            )
            
            # Buscar categorias
            categorias = list(
                context['restaurante'].categorias.filter(
                    nome__icontains=query
                ).values_list('nome', flat=True)[:2]
            )
            
            # Combinar sugestões
            sugestoes = produtos_nomes + produtos_contem + categorias
            
            # Remover duplicatas mantendo ordem
            sugestoes = list(dict.fromkeys(sugestoes))
            
            # Limitar a 8 sugestões
            sugestoes = sugestoes[:8]
        
        return JsonResponse({
            'sugestoes': sugestoes,
            'query': query
        })
