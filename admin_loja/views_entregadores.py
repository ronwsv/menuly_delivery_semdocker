from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from core.models import Entregador, Pedido, AvaliacaoEntregador, OcorrenciaEntrega
from .utils import painel_loja_required as admin_loja_required
import json


@admin_loja_required
def listar_entregadores(request):
    """Lista todos os entregadores com informações de performance"""
    
    # Filtros
    search = request.GET.get('search', '')
    status = request.GET.get('status', 'all')
    
    entregadores = Entregador.objects.all().select_related('usuario')
    
    if search:
        entregadores = entregadores.filter(
            Q(nome__icontains=search) |
            Q(telefone__icontains=search) |
            Q(usuario__username__icontains=search)
        )
    
    if status == 'disponivel':
        entregadores = entregadores.filter(disponivel=True, em_pausa=False)
    elif status == 'em_pausa':
        entregadores = entregadores.filter(em_pausa=True)
    elif status == 'indisponivel':
        entregadores = entregadores.filter(disponivel=False)
    
    # Adicionar estatísticas
    entregadores = entregadores.annotate(
        total_pedidos=Count('pedidos_entrega'),
        media_avaliacoes=Avg('avaliacoes__nota')
    ).order_by('-disponivel', '-nota_media', 'nome')
    
    # Paginação
    paginator = Paginator(entregadores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_entregadores': paginator.count,
        'disponiveis': Entregador.objects.filter(disponivel=True, em_pausa=False).count(),
        'em_pausa': Entregador.objects.filter(em_pausa=True).count(),
        'indisponiveis': Entregador.objects.filter(disponivel=False).count(),
    }
    
    return render(request, 'admin_loja/entregadores_listar.html', context)


@admin_loja_required
def detalhe_entregador(request, entregador_id):
    """Detalhes de um entregador específico"""
    entregador = get_object_or_404(Entregador, id=entregador_id)
    
    # Estatísticas do entregador
    pedidos_entrega = entregador.pedidos_entrega.all().order_by('-created_at')
    avaliacoes = entregador.avaliacoes.all().order_by('-data')
    ocorrencias = entregador.ocorrencias.all().order_by('-data')
    
    # Estatísticas resumidas
    total_entregas = pedidos_entrega.filter(status='entregue').count()
    total_avaliacoes = avaliacoes.count()
    ocorrencias_nao_resolvidas = ocorrencias.filter(resolvido=False).count()
    
    # Últimas atividades
    ultimos_pedidos = pedidos_entrega[:10]
    ultimas_avaliacoes = avaliacoes[:10]
    ultimas_ocorrencias = ocorrencias[:10]
    
    context = {
        'entregador': entregador,
        'total_entregas': total_entregas,
        'total_avaliacoes': total_avaliacoes,
        'ocorrencias_nao_resolvidas': ocorrencias_nao_resolvidas,
        'ultimos_pedidos': ultimos_pedidos,
        'ultimas_avaliacoes': ultimas_avaliacoes,
        'ultimas_ocorrencias': ultimas_ocorrencias,
    }
    
    return render(request, 'admin_loja/entregadores_detalhe.html', context)


@admin_loja_required
def pedidos_aguardando_entregador(request):
    """Lista pedidos que estão aguardando entregador"""
    
    # Pedidos aguardando entregador
    pedidos = Pedido.objects.filter(
        status='aguardando_entregador',
        tipo_entrega='delivery'
    ).select_related('restaurante').order_by('-created_at')
    
    # Entregadores disponíveis
    entregadores_disponiveis = Entregador.objects.filter(
        disponivel=True,
        em_pausa=False
    ).order_by('-nota_media', 'nome')
    
    # Paginação
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular estatísticas adicionais
    pedidos_em_entrega = Pedido.objects.filter(
        status='em_entrega',
        tipo_entrega='delivery'
    ).count()
    
    context = {
        'page_obj': page_obj,
        'pedidos': page_obj.object_list,  # Para compatibilidade
        'entregadores_disponiveis': entregadores_disponiveis,
        'total_pedidos': paginator.count,
        'pedidos_em_entrega': pedidos_em_entrega,
        'tempo_medio_espera': 'N/A',  # Pode implementar cálculo depois
    }
    
    return render(request, 'admin_loja/pedidos_aguardando_entregador.html', context)


@admin_loja_required
def api_entregadores_disponiveis(request):
    """API para listar entregadores disponíveis"""
    entregadores = Entregador.objects.filter(
        disponivel=True,
        em_pausa=False
    ).annotate(
        total_entregas=Count('pedidos_entrega'),
        nota_media=Avg('avaliacoes__nota')
    ).order_by('-nota_media', 'nome')
    
    data = {
        'entregadores': [{
            'id': e.id,
            'nome': e.nome,
            'telefone': e.telefone,
            'nota_media': float(e.nota_media) if e.nota_media else 0.0,
            'total_entregas': e.total_entregas
        } for e in entregadores]
    }
    
    return JsonResponse(data)


@admin_loja_required
@require_http_methods(["POST"])
def atribuir_entregador_manual(request, pedido_id):
    """Atribui manualmente um entregador a um pedido"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    entregador_id = request.POST.get('entregador_id')
    
    if not entregador_id:
        return JsonResponse({
            'success': False,
            'message': 'Selecione um entregador.'
        })
    
    entregador = get_object_or_404(Entregador, id=entregador_id)
    
    # Verificar se o entregador está disponível
    if not entregador.disponivel or entregador.em_pausa:
        return JsonResponse({
            'success': False,
            'message': f'{entregador.nome} não está disponível no momento.'
        })
    
    # Verificar se o pedido pode receber entregador
    if pedido.status not in ['aguardando_entregador', 'pronto']:
        return JsonResponse({
            'success': False,
            'message': 'Este pedido não pode mais receber entregador.'
        })
    
    # Verificar se entregador já tem pedido em andamento
    if entregador.pedidos_entrega.filter(status='em_entrega').exists():
        return JsonResponse({
            'success': False,
            'message': f'{entregador.nome} já tem uma entrega em andamento.'
        })
    
    try:
        # Atribuir entregador
        pedido.entregador = entregador
        pedido.status = 'em_entrega'
        pedido.save()
        
        # Registrar aceite (evitar duplicatas)
        from core.models import AceitePedido
        AceitePedido.objects.get_or_create(
            pedido=pedido,
            entregador=entregador,
            defaults={
                'status': 'aceito',
                'observacoes': f'Atribuição manual pelo lojista {request.user.get_full_name()}'
            }
        )
        
        # Notificar entregador
        from core.notifications import notificar_entregador_atribuido
        notificar_entregador_atribuido(pedido, entregador)
        
        return JsonResponse({
            'success': True,
            'message': f'Pedido #{pedido.numero} atribuído para {entregador.nome} com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao atribuir entregador: {str(e)}'
        })


@admin_loja_required
def ocorrencias_entrega(request):
    """Lista ocorrências de entrega para resolução"""
    
    # Filtros
    status = request.GET.get('status', 'all')
    tipo = request.GET.get('tipo', 'all')
    
    ocorrencias = OcorrenciaEntrega.objects.all().select_related(
        'pedido', 'entregador'
    ).order_by('-data')
    
    if status == 'pendente':
        ocorrencias = ocorrencias.filter(resolvido=False)
    elif status == 'resolvido':
        ocorrencias = ocorrencias.filter(resolvido=True)
    
    if tipo != 'all':
        ocorrencias = ocorrencias.filter(tipo=tipo)
    
    # Paginação
    paginator = Paginator(ocorrencias, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_ocorrencias = OcorrenciaEntrega.objects.count()
    pendentes = OcorrenciaEntrega.objects.filter(resolvido=False).count()
    resolvidas = OcorrenciaEntrega.objects.filter(resolvido=True).count()
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'tipo': tipo,
        'tipos_ocorrencia': OcorrenciaEntrega.TIPO_CHOICES,
        'total_ocorrencias': total_ocorrencias,
        'pendentes': pendentes,
        'resolvidas': resolvidas,
    }
    
    return render(request, 'admin_loja/entregadores_ocorrencias.html', context)


@admin_loja_required
@require_http_methods(["POST"])
def resolver_ocorrencia(request, ocorrencia_id):
    """Marca uma ocorrência como resolvida"""
    ocorrencia = get_object_or_404(OcorrenciaEntrega, id=ocorrencia_id)
    observacoes = request.POST.get('observacoes_resolucao', '').strip()
    
    ocorrencia.resolvido = True
    ocorrencia.observacoes_resolucao = observacoes
    ocorrencia.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Ocorrência marcada como resolvida!'
    })


@admin_loja_required
def relatorio_entregas(request):
    """Relatório de performance dos entregadores"""
    from datetime import datetime, timedelta
    from django.utils import timezone
    from django.db.models import Count, Avg, Sum
    
    # Período do relatório (padrão: últimos 30 dias)
    dias = int(request.GET.get('dias', 30))
    data_inicio = timezone.now() - timedelta(days=dias)
    
    # Estatísticas gerais
    total_entregas = Pedido.objects.filter(
        status='entregue',
        data_entrega__gte=data_inicio,
        entregador__isnull=False
    ).count()
    
    # Performance por entregador
    entregadores_stats = Entregador.objects.filter(
        pedidos_entrega__status='entregue',
        pedidos_entrega__data_entrega__gte=data_inicio
    ).annotate(
        entregas_periodo=Count('pedidos_entrega'),
        nota_media_periodo=Avg('avaliacoes__nota'),
        valor_total_entregas=Sum('pedidos_entrega__valor_entrega')
    ).order_by('-entregas_periodo')
    
    # Tipos de ocorrências mais comuns
    ocorrencias_stats = OcorrenciaEntrega.objects.filter(
        data__gte=data_inicio
    ).values('tipo').annotate(
        total=Count('tipo')
    ).order_by('-total')
    
    context = {
        'dias': dias,
        'data_inicio': data_inicio,
        'total_entregas': total_entregas,
        'entregadores_stats': entregadores_stats,
        'ocorrencias_stats': ocorrencias_stats,
        'total_entregadores': entregadores_stats.count(),
    }
    
    return render(request, 'admin_loja/entregadores_relatorio.html', context)