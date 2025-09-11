from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from core.models import (
    Entregador, Pedido, AceitePedido, AvaliacaoEntregador,
    OcorrenciaEntrega, Usuario
)
from core.notifications import (
    notificar_pedido_aceito, notificar_ocorrencia_entrega
)
from .forms import CadastroEntregadorForm
import json


def entregador_required(view_func):
    """Decorator para verificar se o usuário é um entregador"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('painel_entregador:login')
        
        if request.user.tipo_usuario != 'entregador':
            messages.error(request, 'Acesso negado. Você não é um entregador cadastrado.')
            return redirect('painel_entregador:login')
        
        try:
            request.user.entregador
        except Entregador.DoesNotExist:
            messages.error(request, 'Perfil de entregador não encontrado.')
            return redirect('painel_entregador:login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def login_view(request):
    """Página de login para entregadores"""
    if request.method == 'POST':
        email_or_username = request.POST.get('username')  # Pode ser email ou username
        password = request.POST.get('password')
        
        # Tentar primeiro com o valor como está (pode ser username)
        user = authenticate(request, username=email_or_username, password=password)
        
        # Se não funcionou e parece ser um email, tentar buscar pelo email
        if user is None and '@' in email_or_username:
            try:
                usuario_obj = Usuario.objects.get(email=email_or_username)
                user = authenticate(request, username=usuario_obj.username, password=password)
            except Usuario.DoesNotExist:
                user = None
        
        if user is not None and user.tipo_usuario == 'entregador':
            try:
                entregador = user.entregador
                login(request, user)
                messages.success(request, f'Bem-vindo, {entregador.nome}!')
                return redirect('painel_entregador:dashboard')
            except Entregador.DoesNotExist:
                messages.error(request, 'Perfil de entregador não encontrado.')
        else:
            messages.error(request, 'Credenciais inválidas ou usuário não é um entregador.')
    
    return render(request, 'painel_entregador/login.html')


def cadastro_view(request):
    """Página de cadastro para novos entregadores"""
    print(f"[DEBUG] cadastro_view chamada - método: {request.method}")
    
    if request.method == 'POST':
        print("[DEBUG] POST recebido")
        print(f"[DEBUG] POST data: {request.POST}")
        
        form = CadastroEntregadorForm(request.POST)
        print(f"[DEBUG] Form criado")
        
        if form.is_valid():
            print("[DEBUG] Form é válido")
            try:
                user = form.save()
                print(f"[DEBUG] Usuário criado: {user}")
                messages.success(request, 'Cadastro realizado com sucesso! Agora você pode fazer login.')
                return redirect('painel_entregador:login')
            except Exception as e:
                print(f"[DEBUG] Erro ao salvar: {e}")
                messages.error(request, f'Erro ao criar cadastro: {str(e)}')
        else:
            print(f"[DEBUG] Form inválido - erros: {form.errors}")
            # Adicionar erros específicos para debug
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        print("[DEBUG] GET request")
        form = CadastroEntregadorForm()
    
    print("[DEBUG] Renderizando template")
    return render(request, 'painel_entregador/cadastro.html', {'form': form})


@entregador_required
def dashboard(request):
    """Dashboard principal do entregador"""
    entregador = request.user.entregador
    
    # Estatísticas do dia
    hoje = timezone.now().date()
    pedidos_hoje = entregador.pedidos_entrega.filter(
        created_at__date=hoje,
        status='entregue'
    )
    
    # Pedidos disponíveis para aceite
    pedidos_disponiveis = Pedido.objects.filter(
        status='pronto',
        tipo_entrega='delivery'
    ).order_by('-created_at')[:10]
    
    # Pedido atual em andamento
    pedido_atual = entregador.pedidos_entrega.filter(
        status='em_entrega'
    ).first()
    
    # Estatísticas gerais
    context = {
        'entregador': entregador,
        'pedidos_disponiveis': pedidos_disponiveis,
        'pedido_atual': pedido_atual,
        'entregas_hoje': pedidos_hoje.count(),
        'valor_hoje': sum(p.valor_entrega for p in pedidos_hoje),
        'total_entregas': entregador.total_entregas,
        'nota_media': entregador.nota_media,
    }
    
    return render(request, 'painel_entregador/dashboard.html', context)


@entregador_required
def pedidos_disponiveis(request):
    """Lista todos os pedidos disponíveis para aceite"""
    pedidos = Pedido.objects.filter(
        status='pronto',
        tipo_entrega='delivery'
    ).select_related('restaurante').order_by('-created_at')
    
    # Paginação
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_pedidos': paginator.count,
    }
    
    return render(request, 'painel_entregador/pedidos_disponiveis.html', context)


@entregador_required
@require_http_methods(["POST"])
def aceitar_pedido(request, pedido_id):
    """Aceita um pedido disponível"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    entregador = request.user.entregador
    
    # Verificações
    if not entregador.disponivel or entregador.em_pausa:
        return JsonResponse({
            'success': False,
            'message': 'Você não está disponível para aceitar pedidos.'
        })
    
    if pedido.status != 'pronto':
        return JsonResponse({
            'success': False,
            'message': 'Este pedido não está mais disponível.'
        })
    
    # Verificar se já tem pedido em andamento
    if entregador.pedidos_entrega.filter(status='em_entrega').exists():
        return JsonResponse({
            'success': False,
            'message': 'Você já tem um pedido em andamento. Conclua-o antes de aceitar outro.'
        })
    
    # Aceitar pedido atomicamente
    try:
        with transaction.atomic():
            # Verificar novamente se ainda está disponível (race condition)
            pedido.refresh_from_db()
            if pedido.status != 'pronto':
                return JsonResponse({
                    'success': False,
                    'message': 'Este pedido já foi aceito por outro entregador.'
                })
            
            # Atribuir entregador e alterar status para 'entrega' (saiu para entrega)
            pedido.entregador = entregador
            pedido.status = 'entrega'
            pedido.save()
            
            # Registrar aceite (evitar duplicatas)
            AceitePedido.objects.get_or_create(
                pedido=pedido,
                entregador=entregador,
                defaults={'status': 'aceito'}
            )
            
            # Notificar lojista e cliente
            notificar_pedido_aceito(pedido, entregador)
            
            return JsonResponse({
                'success': True,
                'message': f'Pedido #{pedido.numero} aceito com sucesso!',
                'redirect_url': f'/entregador/pedido/{pedido.id}/'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao aceitar pedido: {str(e)}'
        })


@entregador_required
def meus_pedidos(request):
    """Lista pedidos do entregador"""
    entregador = request.user.entregador
    
    # Filtros
    status_filter = request.GET.get('status', 'all')
    
    pedidos = entregador.pedidos_entrega.select_related('restaurante').order_by('-created_at')
    
    if status_filter != 'all':
        pedidos = pedidos.filter(status=status_filter)
    
    # Paginação
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Pedido.STATUS_CHOICES,
    }
    
    return render(request, 'painel_entregador/meus_pedidos.html', context)


@entregador_required
def detalhe_pedido(request, pedido_id):
    """Detalhes de um pedido específico"""
    pedido = get_object_or_404(
        Pedido.objects.select_related('restaurante').prefetch_related('itens__produto'),
        id=pedido_id,
        entregador=request.user.entregador
    )
    
    # Ocorrências do pedido
    ocorrencias = pedido.ocorrencias.filter(
        entregador=request.user.entregador
    ).order_by('-data')
    
    context = {
        'pedido': pedido,
        'ocorrencias': ocorrencias,
        'tipos_ocorrencia': OcorrenciaEntrega.TIPO_CHOICES,
    }
    
    return render(request, 'painel_entregador/detalhe_pedido.html', context)


@entregador_required
@require_http_methods(["POST"])
def alterar_status_pedido(request, pedido_id):
    """Altera o status do pedido (para entregador)"""
    pedido = get_object_or_404(Pedido, id=pedido_id, entregador=request.user.entregador)
    novo_status = request.POST.get('status')
    
    # Validar transições permitidas para entregador
    transicoes_permitidas = {
        'em_entrega': ['entregue'],  # Entregador só pode marcar como entregue
    }
    
    if pedido.status not in transicoes_permitidas:
        return JsonResponse({
            'success': False,
            'message': 'Não é possível alterar o status deste pedido.'
        })
    
    if novo_status not in transicoes_permitidas[pedido.status]:
        return JsonResponse({
            'success': False,
            'message': 'Transição de status não permitida.'
        })
    
    # Alterar status
    pedido.status = novo_status
    if novo_status == 'entregue':
        pedido.data_entrega = timezone.now()
    
    pedido.save()
    
    # Criar histórico
    from core.models import HistoricoStatusPedido
    HistoricoStatusPedido.objects.create(
        pedido=pedido,
        status_anterior=pedido.status,
        status_novo=novo_status,
        usuario=request.user,
        observacoes=f'Status alterado pelo entregador {request.user.entregador.nome}'
    )
    
    # Atualizar contador de entregas
    if novo_status == 'entregue':
        entregador = request.user.entregador
        entregador.total_entregas += 1
        entregador.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Status alterado para {dict(Pedido.STATUS_CHOICES)[novo_status]}.'
    })


@entregador_required
@require_http_methods(["POST"])
def registrar_ocorrencia(request, pedido_id):
    """Registra uma ocorrência na entrega"""
    pedido = get_object_or_404(Pedido, id=pedido_id, entregador=request.user.entregador)
    
    tipo = request.POST.get('tipo')
    descricao = request.POST.get('descricao', '').strip()
    
    if not tipo or not descricao:
        return JsonResponse({
            'success': False,
            'message': 'Tipo e descrição da ocorrência são obrigatórios.'
        })
    
    # Criar ocorrência
    ocorrencia = OcorrenciaEntrega.objects.create(
        pedido=pedido,
        entregador=request.user.entregador,
        tipo=tipo,
        descricao=descricao
    )
    
    # Notificar lojista
    notificar_ocorrencia_entrega(ocorrencia)
    
    return JsonResponse({
        'success': True,
        'message': 'Ocorrência registrada com sucesso!'
    })


@entregador_required
def avaliacoes(request):
    """Lista avaliações recebidas pelo entregador"""
    entregador = request.user.entregador
    
    avaliacoes = entregador.avaliacoes.select_related('pedido').order_by('-data')
    
    # Paginação
    paginator = Paginator(avaliacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'nota_media': entregador.nota_media,
        'total_avaliacoes': entregador.total_avaliacoes,
    }
    
    return render(request, 'painel_entregador/avaliacoes.html', context)


@entregador_required
def perfil(request):
    """Página de perfil do entregador"""
    entregador = request.user.entregador
    
    if request.method == 'POST':
        # Atualizar dados do perfil
        entregador.nome = request.POST.get('nome', entregador.nome)
        entregador.telefone = request.POST.get('telefone', entregador.telefone)
        entregador.cnh = request.POST.get('cnh', entregador.cnh)
        entregador.veiculo = request.POST.get('veiculo', entregador.veiculo)
        entregador.dados_bancarios = request.POST.get('dados_bancarios', entregador.dados_bancarios)
        entregador.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('painel_entregador:perfil')
    
    context = {
        'entregador': entregador,
    }
    
    return render(request, 'painel_entregador/perfil.html', context)


@entregador_required
@require_http_methods(["POST"])
def alterar_disponibilidade(request):
    """Altera a disponibilidade do entregador"""
    entregador = request.user.entregador
    
    disponivel = request.POST.get('disponivel') == 'true'
    em_pausa = request.POST.get('em_pausa') == 'true'
    
    entregador.disponivel = disponivel
    entregador.em_pausa = em_pausa
    entregador.save()
    
    status_texto = 'disponível' if disponivel and not em_pausa else 'indisponível'
    if em_pausa:
        status_texto = 'em pausa'
    
    return JsonResponse({
        'success': True,
        'message': f'Status alterado para: {status_texto}',
        'status': entregador.status_display
    })


@entregador_required
def relatorios(request):
    """Relatórios e estatísticas do entregador"""
    entregador = request.user.entregador
    
    # Período do relatório
    periodo = request.GET.get('periodo', 'mes')  # semana, mes, trimestre
    
    hoje = timezone.now().date()
    
    if periodo == 'semana':
        from datetime import timedelta
        data_inicio = hoje - timedelta(days=7)
    elif periodo == 'trimestre':
        from datetime import timedelta
        data_inicio = hoje - timedelta(days=90)
    else:  # mês
        data_inicio = hoje.replace(day=1)
    
    # Pedidos do período
    pedidos = entregador.pedidos_entrega.filter(
        created_at__date__gte=data_inicio,
        status='entregue'
    )
    
    # Estatísticas
    total_entregas = pedidos.count()
    total_ganhos = sum(p.valor_entrega for p in pedidos)
    media_diaria = total_ganhos / max((hoje - data_inicio).days, 1)
    valor_medio_entrega = total_ganhos / total_entregas if total_entregas > 0 else 0
    
    # Avaliações do período
    avaliacoes_periodo = entregador.avaliacoes.filter(
        data__date__gte=data_inicio
    )
    
    context = {
        'entregador': entregador,
        'periodo': periodo,
        'data_inicio': data_inicio,
        'total_entregas': total_entregas,
        'total_ganhos': total_ganhos,
        'media_diaria': media_diaria,
        'valor_medio_entrega': valor_medio_entrega,
        'avaliacoes_periodo': avaliacoes_periodo.count(),
        'pedidos_periodo': pedidos.order_by('-created_at')[:20],
    }
    
    return render(request, 'painel_entregador/relatorios.html', context)
