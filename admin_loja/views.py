from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms


# Personalizar loja
from .forms import LogoForm, BannerForm, ImpressoraForm, CategoriaForm, ProdutoForm
@login_required
def admin_loja_personalizar_loja(request):
    from core.models import Restaurante
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/personalizar_loja.html', {'msg': 'Você não tem permissão para personalizar esta loja.'})
    logo_url = restaurante.logo.url if restaurante.logo else None
    banner_url = restaurante.banner.url if restaurante.banner else None
    msg = None
    logo_form = LogoForm(instance=restaurante)
    banner_form = BannerForm(instance=restaurante)
    if request.method == 'POST':
        if 'logo' in request.FILES:
            logo_form = LogoForm(request.POST, request.FILES, instance=restaurante)
            if logo_form.is_valid():
                logo_form.save()
                msg = 'Logo atualizada com sucesso!'
                logo_url = restaurante.logo.url if restaurante.logo else None
        if 'banner' in request.FILES:
            banner_form = BannerForm(request.POST, request.FILES, instance=restaurante)
            if banner_form.is_valid():
                banner_form.save()
                msg = 'Banner atualizado com sucesso!'
                banner_url = restaurante.banner.url if restaurante.banner else None
    return render(request, 'admin_loja/personalizar_loja.html', {
        'form': logo_form,
        'banner_form': banner_form,
        'logo_url': logo_url,
        'banner_url': banner_url,
        'msg': msg
    })
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms

# Logout do lojista
@login_required
def admin_loja_logout(request):
    logout(request)
    return render(request, 'admin_loja/logout.html')

# Personalizar loja
@login_required
def admin_loja_personalizar_loja(request):
    # Página inicial de personalização da loja
    return render(request, 'admin_loja/personalizar_loja.html')

# Configuração de frete
@login_required
def admin_loja_configurar_frete(request):
    class FreteForm(forms.Form):
        frete_fixo = forms.BooleanField(label='Usar Frete Fixo?', required=False)
        valor_frete_fixo = forms.DecimalField(label='Valor do Frete Fixo', max_digits=7, decimal_places=2, required=False)
        cep_base = forms.CharField(label='CEP da Loja', max_length=10)
        valor_frete_padrao = forms.DecimalField(label='Valor do Frete Padrão', max_digits=7, decimal_places=2, required=False)
        valor_adicional_km = forms.DecimalField(label='Valor Adicional por Km', max_digits=7, decimal_places=2, required=False)
        raio_limite_km = forms.DecimalField(label='Raio Máximo de Entrega (km)', max_digits=5, decimal_places=2, required=False, help_text='Deixe em branco para sem limite')

        def clean(self):
            cleaned_data = super().clean()
            frete_fixo = cleaned_data.get('frete_fixo')
            valor_frete_fixo = cleaned_data.get('valor_frete_fixo')
            valor_frete_padrao = cleaned_data.get('valor_frete_padrao')
            valor_adicional_km = cleaned_data.get('valor_adicional_km')
            cep_base = cleaned_data.get('cep_base')

            if not cep_base:
                self.add_error('cep_base', 'Informe o CEP da Loja.')

            if frete_fixo:
                if valor_frete_fixo is None:
                    self.add_error('valor_frete_fixo', 'Informe o valor do frete fixo.')
            else:
                if valor_frete_padrao is None:
                    self.add_error('valor_frete_padrao', 'Informe o valor do frete padrão.')
                if valor_adicional_km is None:
                    self.add_error('valor_adicional_km', 'Informe o valor adicional por km.')
            return cleaned_data

    # Aqui futuramente vamos buscar/salvar as configurações reais do banco
    from core.models import Restaurante
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    initial = {}
    if restaurante:
        initial = {
            'frete_fixo': restaurante.frete_fixo,
            'valor_frete_fixo': restaurante.valor_frete_fixo,
            'cep_base': restaurante.cep,
            'valor_frete_padrao': restaurante.valor_frete_padrao,
            'valor_adicional_km': restaurante.valor_adicional_km,
            'raio_limite_km': restaurante.raio_limite_km,
        }

    if request.method == 'POST':
        form = FreteForm(request.POST)
        if form.is_valid():
            if restaurante:
                restaurante.frete_fixo = form.cleaned_data['frete_fixo']
                restaurante.valor_frete_fixo = form.cleaned_data['valor_frete_fixo'] if form.cleaned_data['frete_fixo'] else None
                restaurante.cep = form.cleaned_data['cep_base']
                restaurante.valor_frete_padrao = form.cleaned_data['valor_frete_padrao'] if not form.cleaned_data['frete_fixo'] else None
                restaurante.valor_adicional_km = form.cleaned_data['valor_adicional_km'] if not form.cleaned_data['frete_fixo'] else None
                restaurante.raio_limite_km = form.cleaned_data['raio_limite_km']
                restaurante.save()
            msg = 'Configurações salvas com sucesso!'
            return render(request, 'admin_loja/configurar_frete.html', {'form': form, 'msg': msg})
        else:
            return render(request, 'admin_loja/configurar_frete.html', {'form': form})
    else:
        form = FreteForm(initial=initial)
    return render(request, 'admin_loja/configurar_frete.html', {'form': form})


# Avançar status do pedido
@login_required
def admin_loja_avancar_status_pedido(request, pedido_id):
    from core.models import Pedido
    pedido = Pedido.objects.get(id=pedido_id, restaurante__proprietario=request.user)
    # Definir o fluxo de status
    fluxo = ['novo', 'preparo', 'pronto', 'entrega', 'finalizado']
    try:
        idx = fluxo.index(pedido.status)
        if idx < len(fluxo) - 1:
            pedido.status = fluxo[idx + 1]
            pedido.save()
    except ValueError:
        pass
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin-loja/pedidos/'))

class AdminLojaLoginForm(forms.Form):
    username = forms.CharField(label='Usuário')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')

def admin_loja_login(request):
    error = None
    if request.method == 'POST':
        form = AdminLojaLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None and hasattr(user, 'tipo_usuario') and user.tipo_usuario == 'lojista':
                login(request, user)
                return redirect('admin_loja:dashboard')
            else:
                error = 'Usuário ou senha inválidos, ou você não é um lojista.'
    else:
        form = AdminLojaLoginForm()
    return render(request, 'admin_loja/login.html', {'form': form, 'error': error})

@login_required
def admin_loja_dashboard(request):
    # Aqui futuramente vamos filtrar para mostrar só dados da loja do lojista
    return render(request, 'admin_loja/dashboard.html')
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms


from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_loja/dashboard.html'
    login_url = 'admin_loja:login'


# Página de pedidos do lojista
from django.contrib.auth.decorators import login_required
@login_required

def admin_loja_pedidos(request):
    # Buscar restaurantes do lojista logado
    restaurantes = request.user.restaurantes.all()
    pedidos = []
    status_list = ['novo', 'preparo', 'pronto', 'entrega', 'finalizado']
    pedidos_por_status = {status: [] for status in status_list}
    if restaurantes.exists():
        from core.models import Pedido
        pedidos = Pedido.objects.filter(restaurante__in=restaurantes).order_by('created_at')
        for pedido in pedidos:
            if pedido.status in pedidos_por_status:
                pedidos_por_status[pedido.status].append(pedido)
    return render(request, 'admin_loja/pedidos.html', {'pedidos_por_status': pedidos_por_status})

# Visualização de cupom do pedido
from django.shortcuts import get_object_or_404
@login_required
def admin_loja_cupom_pedido(request, pedido_id):
    from core.models import Pedido, ItemPedido
    pedido = get_object_or_404(Pedido, id=pedido_id, restaurante__proprietario=request.user)
    itens = pedido.itens.all() if hasattr(pedido, 'itens') else []
    return render(request, 'admin_loja/cupom_pedido.html', {'pedido': pedido, 'itens': itens})


# ==================== VIEWS DE IMPRESSORAS ====================

@login_required
def admin_loja_impressoras(request):
    """Lista todas as impressoras do restaurante"""
    from core.models import Restaurante
    from .models import Impressora
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/impressoras.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    impressoras = Impressora.objects.filter(restaurante=restaurante).order_by('-created_at')
    
    return render(request, 'admin_loja/impressoras.html', {
        'impressoras': impressoras,
        'restaurante': restaurante
    })

@login_required
def admin_loja_impressora_cadastrar(request):
    """Cadastrar nova impressora"""
    from core.models import Restaurante
    from .models import Impressora
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/impressora_form.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    if request.method == 'POST':
        form = ImpressoraForm(request.POST)
        if form.is_valid():
            impressora = form.save(commit=False)
            impressora.restaurante = restaurante
            impressora.save()
            return redirect('admin_loja:impressoras')
    else:
        form = ImpressoraForm()
    
    return render(request, 'admin_loja/impressora_form.html', {
        'form': form,
        'titulo': 'Cadastrar Impressora'
    })

@login_required
def admin_loja_impressora_editar(request, impressora_id):
    """Editar impressora existente"""
    from .models import Impressora
    
    impressora = get_object_or_404(
        Impressora, 
        id=impressora_id, 
        restaurante__proprietario=request.user
    )
    
    if request.method == 'POST':
        form = ImpressoraForm(request.POST, instance=impressora)
        if form.is_valid():
            form.save()
            return redirect('admin_loja:impressoras')
    else:
        form = ImpressoraForm(instance=impressora)
    
    return render(request, 'admin_loja/impressora_form.html', {
        'form': form,
        'impressora': impressora,
        'titulo': 'Editar Impressora'
    })

@login_required
def admin_loja_impressora_deletar(request, impressora_id):
    """Deletar impressora"""
    from .models import Impressora
    
    impressora = get_object_or_404(
        Impressora, 
        id=impressora_id, 
        restaurante__proprietario=request.user
    )
    
    impressora.delete()
    return redirect('admin_loja:impressoras')

@login_required
def admin_loja_impressora_testar(request, impressora_id):
    """Testar impressora"""
    from .models import Impressora
    import requests
    import json
    
    impressora = get_object_or_404(
        Impressora, 
        id=impressora_id, 
        restaurante__proprietario=request.user
    )
    
    # Dados para teste de impressão
    dados_teste = {
        'impressora': {
            'nome': impressora.nome,
            'tipo_conexao': impressora.tipo_conexao,
            'connection_string': impressora.get_connection_string(),
            'largura_papel': impressora.largura_papel,
            'cortar_papel': impressora.cortar_papel
        },
        'conteudo': f"""
=============================
TESTE DE IMPRESSÃO
=============================
Impressora: {impressora.nome}
Tipo: {impressora.get_tipo_conexao_display()}
Data/Hora: {impressora.created_at.strftime('%d/%m/%Y %H:%M')}
=============================
Este é um teste de impressão
para verificar se a impressora
está funcionando corretamente.
=============================
        """.strip()
    }
    
    try:
        # Endpoint local para teste de impressão (simulado)
        # Em um cenário real, você faria uma requisição para um serviço local
        response = requests.post(
            'http://localhost:8080/api/print-test',
            json=dados_teste,
            timeout=5
        )
        
        if response.status_code == 200:
            mensagem = 'Teste de impressão enviado com sucesso!'
            tipo_msg = 'success'
        else:
            mensagem = f'Erro ao enviar teste: {response.text}'
            tipo_msg = 'error'
            
    except requests.exceptions.RequestException as e:
        mensagem = f'Erro de conexão com serviço de impressão: {str(e)}'
        tipo_msg = 'error'
    except Exception as e:
        mensagem = f'Erro interno: {str(e)}'
        tipo_msg = 'error'
    
    return render(request, 'admin_loja/impressora_teste.html', {
        'impressora': impressora,
        'mensagem': mensagem,
        'tipo_msg': tipo_msg
    })


# ==================== VIEWS DE CATEGORIAS ====================

@login_required
def admin_loja_categorias(request):
    """Lista todas as categorias do restaurante"""
    from core.models import Restaurante, Categoria
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/categorias.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    categorias = Categoria.objects.filter(restaurante=restaurante).order_by('ordem', 'nome')
    
    return render(request, 'admin_loja/categorias.html', {
        'categorias': categorias,
        'restaurante': restaurante
    })

@login_required
def admin_loja_categoria_cadastrar(request):
    """Cadastrar nova categoria"""
    from core.models import Restaurante, Categoria
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/categoria_form.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.restaurante = restaurante
            categoria.save()
            return redirect('admin_loja:categorias')
    else:
        form = CategoriaForm()
    
    return render(request, 'admin_loja/categoria_form.html', {
        'form': form,
        'titulo': 'Nova Categoria',
        'produtos_disponiveis': 0
    })

@login_required
def admin_loja_categoria_editar(request, categoria_id):
    """Editar categoria existente"""
    from core.models import Categoria
    
    categoria = get_object_or_404(
        Categoria, 
        id=categoria_id, 
        restaurante__proprietario=request.user
    )
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('admin_loja:categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    # Get statistics if editing existing category
    produtos_disponiveis = 0
    if categoria:
        produtos_disponiveis = categoria.produtos.filter(disponivel=True).count()
    
    return render(request, 'admin_loja/categoria_form.html', {
        'form': form,
        'categoria': categoria,
        'titulo': 'Editar Categoria',
        'produtos_disponiveis': produtos_disponiveis
    })

@login_required
def admin_loja_categoria_deletar(request, categoria_id):
    """Deletar categoria"""
    from core.models import Categoria
    
    categoria = get_object_or_404(
        Categoria, 
        id=categoria_id, 
        restaurante__proprietario=request.user
    )
    
    # Verificar se há produtos na categoria
    if categoria.produtos.exists():
        return render(request, 'admin_loja/categorias.html', {
            'categorias': Categoria.objects.filter(restaurante=categoria.restaurante).order_by('ordem', 'nome'),
            'restaurante': categoria.restaurante,
            'error_msg': 'Não é possível deletar categoria com produtos. Mova os produtos para outra categoria primeiro.'
        })
    
    categoria.delete()
    return redirect('admin_loja:categorias')

@login_required 
def admin_loja_categoria_toggle_ativo(request, categoria_id):
    """Toggle status ativo da categoria via AJAX"""
    from core.models import Categoria
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    categoria = get_object_or_404(
        Categoria, 
        id=categoria_id, 
        restaurante__proprietario=request.user
    )
    
    categoria.ativo = not categoria.ativo
    categoria.save()
    
    return JsonResponse({
        'success': True,
        'ativo': categoria.ativo,
        'status_text': 'Ativa' if categoria.ativo else 'Inativa'
    })


# ==================== VIEWS DE PRODUTOS ====================

@login_required
def admin_loja_produtos(request):
    """Lista todos os produtos do restaurante"""
    from core.models import Restaurante, Produto, Categoria
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/produtos.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')
    
    produtos = Produto.objects.filter(restaurante=restaurante)
    
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)
    
    if status == 'disponivel':
        produtos = produtos.filter(disponivel=True)
    elif status == 'indisponivel':
        produtos = produtos.filter(disponivel=False)
    elif status == 'destaque':
        produtos = produtos.filter(destaque=True)
    
    produtos = produtos.select_related('categoria').order_by('categoria__ordem', 'ordem', 'nome')
    categorias = Categoria.objects.filter(restaurante=restaurante, ativo=True).order_by('ordem', 'nome')
    
    return render(request, 'admin_loja/produtos.html', {
        'produtos': produtos,
        'categorias': categorias,
        'restaurante': restaurante,
        'filtro_categoria': categoria_id,
        'filtro_status': status
    })

@login_required
def admin_loja_produto_cadastrar(request):
    """Cadastrar novo produto"""
    from core.models import Restaurante, Produto
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/produto_form.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, restaurante=restaurante)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.restaurante = restaurante
            produto.save()
            return redirect('admin_loja:produtos')
    else:
        form = ProdutoForm(restaurante=restaurante)
    
    return render(request, 'admin_loja/produto_form.html', {
        'form': form,
        'titulo': 'Novo Produto'
    })

@login_required
def admin_loja_produto_editar(request, produto_id):
    """Editar produto existente"""
    from core.models import Produto
    
    produto = get_object_or_404(
        Produto, 
        id=produto_id, 
        restaurante__proprietario=request.user
    )
    
    if request.method == 'POST':
        form = ProdutoForm(
            request.POST, 
            request.FILES, 
            instance=produto,
            restaurante=produto.restaurante
        )
        if form.is_valid():
            form.save()
            return redirect('admin_loja:produtos')
    else:
        form = ProdutoForm(instance=produto, restaurante=produto.restaurante)
    
    return render(request, 'admin_loja/produto_form.html', {
        'form': form,
        'produto': produto,
        'titulo': 'Editar Produto'
    })

@login_required
def admin_loja_produto_deletar(request, produto_id):
    """Deletar produto"""
    from core.models import Produto
    
    produto = get_object_or_404(
        Produto, 
        id=produto_id, 
        restaurante__proprietario=request.user
    )
    
    produto.delete()
    return redirect('admin_loja:produtos')

@login_required
def admin_loja_produto_toggle_disponivel(request, produto_id):
    """Toggle disponibilidade do produto via AJAX"""
    from core.models import Produto
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    produto = get_object_or_404(
        Produto, 
        id=produto_id, 
        restaurante__proprietario=request.user
    )
    
    produto.disponivel = not produto.disponivel
    produto.save()
    
    return JsonResponse({
        'success': True,
        'disponivel': produto.disponivel,
        'status_text': 'Disponível' if produto.disponivel else 'Esgotado'
    })

@login_required
def admin_loja_produto_toggle_destaque(request, produto_id):
    """Toggle destaque do produto via AJAX"""
    from core.models import Produto
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    produto = get_object_or_404(
        Produto, 
        id=produto_id, 
        restaurante__proprietario=request.user
    )
    
    produto.destaque = not produto.destaque
    produto.save()
    
    return JsonResponse({
        'success': True,
        'destaque': produto.destaque,
        'status_text': 'Em destaque' if produto.destaque else 'Normal'
    })


# ==================== VIEWS DE ORDENAÇÃO (DRAG & DROP) ====================

@login_required
def admin_loja_categoria_reorder(request):
    """Reordenar categorias via AJAX"""
    from core.models import Categoria
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    try:
        data = json.loads(request.body)
        categoria_ids = data.get('categoria_ids', [])
        
        # Atualizar ordem das categorias
        for index, categoria_id in enumerate(categoria_ids):
            Categoria.objects.filter(
                id=categoria_id,
                restaurante__proprietario=request.user
            ).update(ordem=index + 1)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def admin_loja_produto_reorder(request):
    """Reordenar produtos via AJAX"""
    from core.models import Produto
    from django.http import JsonResponse
    import json
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    try:
        data = json.loads(request.body)
        produto_ids = data.get('produto_ids', [])
        
        # Atualizar ordem dos produtos
        for index, produto_id in enumerate(produto_ids):
            Produto.objects.filter(
                id=produto_id,
                restaurante__proprietario=request.user
            ).update(ordem=index + 1)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
