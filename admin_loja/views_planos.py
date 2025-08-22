# ==================== VIEWS DE GESTÃO DE PLANOS ====================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, date
from .utils import painel_loja_required, obter_restaurante_usuario
from core.models import Plano, Restaurante
from django import forms

class UpgradePlanoForm(forms.Form):
    """Form para solicitar upgrade de plano"""
    
    MOTIVO_CHOICES = [
        ('limite_pedidos', 'Atingindo limite de pedidos'),
        ('limite_produtos', 'Preciso de mais produtos'),
        ('recursos_avancados', 'Preciso de recursos avançados'),
        ('multi_loja', 'Preciso de múltiplas lojas'),
        ('outro', 'Outro motivo'),
    ]
    
    plano_desejado = forms.ModelChoiceField(
        queryset=Plano.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Plano Desejado'
    )
    
    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Motivo do Upgrade'
    )
    
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Observações adicionais (opcional)'
        }),
        required=False,
        label='Observações'
    )

@painel_loja_required
def planos_meu_plano(request):
    """Página para visualizar o plano atual e estatísticas de uso"""
    restaurante = obter_restaurante_usuario(request.user)
    
    if not restaurante:
        messages.error(request, 'Restaurante não encontrado.')
        return redirect('admin_loja:dashboard')
    
    # Estatísticas de uso do mês atual
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    stats = {
        'pedidos_mes': restaurante.pedidos.filter(
            created_at__date__gte=inicio_mes,
            created_at__date__lte=hoje
        ).exclude(status='cancelado').count(),
        
        'produtos_total': restaurante.produtos.count(),
        
        'funcionarios_total': restaurante.funcionarios.count(),
        
        'dias_ate_vencimento': restaurante.dias_ate_vencimento(),
    }
    
    # Verificar se está próximo dos limites
    alertas = []
    
    if restaurante.plano:
        # Alerta de pedidos
        if restaurante.plano.limite_pedidos_mes:
            percentual_pedidos = (stats['pedidos_mes'] / restaurante.plano.limite_pedidos_mes) * 100
            if percentual_pedidos >= 80:
                alertas.append({
                    'tipo': 'warning' if percentual_pedidos < 95 else 'danger',
                    'titulo': 'Limite de pedidos',
                    'mensagem': f'Você usou {percentual_pedidos:.0f}% do limite mensal de pedidos.'
                })
        
        # Alerta de produtos
        if restaurante.plano.limite_produtos:
            percentual_produtos = (stats['produtos_total'] / restaurante.plano.limite_produtos) * 100
            if percentual_produtos >= 80:
                alertas.append({
                    'tipo': 'warning' if percentual_produtos < 95 else 'danger',
                    'titulo': 'Limite de produtos',
                    'mensagem': f'Você usou {percentual_produtos:.0f}% do limite de produtos cadastrados.'
                })
        
        # Alerta de vencimento
        if stats['dias_ate_vencimento'] is not None and stats['dias_ate_vencimento'] <= 7:
            if stats['dias_ate_vencimento'] < 0:
                alertas.append({
                    'tipo': 'danger',
                    'titulo': 'Plano vencido',
                    'mensagem': f'Seu plano venceu há {abs(stats["dias_ate_vencimento"])} dias. Regularize para continuar usando.'
                })
            else:
                alertas.append({
                    'tipo': 'warning',
                    'titulo': 'Vencimento próximo',
                    'mensagem': f'Seu plano vence em {stats["dias_ate_vencimento"]} dias.'
                })
    
    context = {
        'restaurante': restaurante,
        'stats': stats,
        'alertas': alertas,
    }
    
    return render(request, 'admin_loja/planos_meu_plano.html', context)

@painel_loja_required
def planos_comparar(request):
    """Página para comparar todos os planos disponíveis"""
    restaurante = obter_restaurante_usuario(request.user)
    planos = Plano.objects.filter(ativo=True).order_by('ordem_exibicao')
    
    context = {
        'restaurante': restaurante,
        'planos': planos,
    }
    
    return render(request, 'admin_loja/planos_comparar.html', context)

@painel_loja_required
def planos_solicitar_upgrade(request):
    """Página para solicitar upgrade de plano"""
    restaurante = obter_restaurante_usuario(request.user)
    
    if not restaurante:
        messages.error(request, 'Restaurante não encontrado.')
        return redirect('admin_loja:dashboard')
    
    # Filtrar apenas planos superiores ao atual
    planos_disponiveis = Plano.objects.filter(ativo=True)
    if restaurante.plano:
        planos_disponiveis = planos_disponiveis.filter(
            preco_mensal__gt=restaurante.plano.preco_mensal
        )
    
    if request.method == 'POST':
        form = UpgradePlanoForm(request.POST)
        form.fields['plano_desejado'].queryset = planos_disponiveis
        
        if form.is_valid():
            # Simular envio da solicitação (aqui você integraria com sistema de vendas)
            solicitacao_data = {
                'restaurante': restaurante.nome,
                'plano_atual': restaurante.plano.get_nome_display() if restaurante.plano else 'Nenhum',
                'plano_desejado': form.cleaned_data['plano_desejado'].get_nome_display(),
                'motivo': form.cleaned_data['motivo'],
                'observacoes': form.cleaned_data['observacoes'],
                'data_solicitacao': timezone.now().isoformat(),
                'usuario_email': request.user.email,
            }
            
            # Aqui você salvaria no banco ou enviaria por email
            print(f"SOLICITAÇÃO DE UPGRADE: {solicitacao_data}")
            
            messages.success(request, 
                f'Solicitação de upgrade para {form.cleaned_data["plano_desejado"].get_nome_display()} '
                f'enviada com sucesso! Nossa equipe entrará em contato em até 24 horas.')
            
            return redirect('admin_loja:planos_meu_plano')
    else:
        form = UpgradePlanoForm()
        form.fields['plano_desejado'].queryset = planos_disponiveis
    
    context = {
        'form': form,
        'restaurante': restaurante,
        'planos_disponiveis': planos_disponiveis,
    }
    
    return render(request, 'admin_loja/planos_solicitar_upgrade.html', context)

@painel_loja_required
def planos_historico_uso(request):
    """Página com histórico de uso e estatísticas detalhadas"""
    restaurante = obter_restaurante_usuario(request.user)
    
    if not restaurante:
        messages.error(request, 'Restaurante não encontrado.')
        return redirect('admin_loja:dashboard')
    
    # Estatísticas dos últimos 6 meses
    hoje = timezone.now().date()
    estatisticas_mensais = []
    
    for i in range(6):
        # Calcular primeiro e último dia do mês
        if i == 0:
            inicio_mes = hoje.replace(day=1)
            fim_mes = hoje
        else:
            mes_ref = hoje.replace(day=1) - timedelta(days=1)
            for _ in range(i-1):
                mes_ref = mes_ref.replace(day=1) - timedelta(days=1)
            
            inicio_mes = mes_ref.replace(day=1)
            # Último dia do mês
            if mes_ref.month == 12:
                proximo_mes = mes_ref.replace(year=mes_ref.year + 1, month=1, day=1)
            else:
                proximo_mes = mes_ref.replace(month=mes_ref.month + 1, day=1)
            fim_mes = proximo_mes - timedelta(days=1)
        
        pedidos_mes = restaurante.pedidos.filter(
            created_at__date__gte=inicio_mes,
            created_at__date__lte=fim_mes
        ).exclude(status='cancelado').count()
        
        vendas_mes = restaurante.pedidos.filter(
            created_at__date__gte=inicio_mes,
            created_at__date__lte=fim_mes,
            status='finalizado'
        ).aggregate(total=models.Sum('total'))['total'] or 0
        
        estatisticas_mensais.append({
            'mes': inicio_mes.strftime('%B %Y'),
            'pedidos': pedidos_mes,
            'vendas': vendas_mes,
        })
    
    estatisticas_mensais.reverse()  # Ordem cronológica
    
    # Uso atual vs limites
    uso_atual = {
        'produtos': {
            'atual': restaurante.produtos.count(),
            'limite': restaurante.plano.limite_produtos if restaurante.plano else None,
        },
        'funcionarios': {
            'atual': restaurante.funcionarios.count(),
            'limite': restaurante.plano.limite_funcionarios if restaurante.plano else None,
        },
        'pedidos_mes': {
            'atual': estatisticas_mensais[-1]['pedidos'] if estatisticas_mensais else 0,
            'limite': restaurante.plano.limite_pedidos_mes if restaurante.plano else None,
        }
    }
    
    context = {
        'restaurante': restaurante,
        'estatisticas_mensais': estatisticas_mensais,
        'uso_atual': uso_atual,
    }
    
    return render(request, 'admin_loja/planos_historico_uso.html', context)

@painel_loja_required
def planos_api_verificar_limite(request):
    """API para verificar se pode executar uma ação baseada nos limites do plano"""
    
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    acao = request.GET.get('acao')
    restaurante = obter_restaurante_usuario(request.user)
    
    if not restaurante:
        return JsonResponse({'success': False, 'error': 'Restaurante não encontrado'})
    
    resultado = {'success': True, 'pode_executar': True, 'mensagem': ''}
    
    if acao == 'criar_produto':
        if not restaurante.pode_criar_produto():
            resultado.update({
                'pode_executar': False,
                'mensagem': f'Limite de {restaurante.plano.limite_produtos} produtos atingido. Faça upgrade do plano.',
                'limite_atual': restaurante.produtos.count(),
                'limite_maximo': restaurante.plano.limite_produtos
            })
    
    elif acao == 'criar_funcionario':
        if not restaurante.pode_criar_funcionario():
            resultado.update({
                'pode_executar': False,
                'mensagem': f'Limite de {restaurante.plano.limite_funcionarios} funcionários atingido. Faça upgrade do plano.',
                'limite_atual': restaurante.funcionarios.count(),
                'limite_maximo': restaurante.plano.limite_funcionarios
            })
    
    elif acao == 'processar_pedido':
        if not restaurante.pode_processar_pedido():
            resultado.update({
                'pode_executar': False,
                'mensagem': f'Limite mensal de {restaurante.plano.limite_pedidos_mes} pedidos atingido. Faça upgrade do plano.',
                'limite_maximo': restaurante.plano.limite_pedidos_mes
            })
    
    else:
        resultado.update({
            'success': False,
            'error': 'Ação não reconhecida'
        })
    
    return JsonResponse(resultado)

@painel_loja_required
def processar_upgrade(request):
    """View para processar o upgrade de plano do lojista"""
    
    if request.method != 'POST':
        messages.error(request, 'Método não permitido.')
        return redirect('admin_loja:planos_comparar')
    
    restaurante = obter_restaurante_usuario(request.user)
    
    if not restaurante:
        messages.error(request, 'Restaurante não encontrado.')
        return redirect('admin_loja:dashboard')
    
    plano_id = request.POST.get('plano_id')
    
    if not plano_id:
        messages.error(request, 'Plano não especificado.')
        return redirect('admin_loja:planos_comparar')
    
    try:
        novo_plano = Plano.objects.get(id=plano_id, ativo=True)
    except Plano.DoesNotExist:
        messages.error(request, 'Plano não encontrado.')
        return redirect('admin_loja:planos_comparar')
    
    # Verificar se é realmente um upgrade
    if restaurante.plano and novo_plano.preco_mensal <= restaurante.plano.preco_mensal:
        messages.error(request, 'Apenas upgrades são permitidos.')
        return redirect('admin_loja:planos_comparar')
    
    # Atualizar o plano do restaurante
    plano_anterior = restaurante.plano.titulo if restaurante.plano else "Nenhum"
    restaurante.plano = novo_plano
    restaurante.data_vencimento_plano = timezone.now().date() + timedelta(days=30)
    restaurante.save()
    
    # Log da alteração (você pode implementar um modelo de histórico aqui)
    print(f"UPGRADE REALIZADO: {restaurante.nome} - {plano_anterior} -> {novo_plano.titulo}")
    
    messages.success(request, 
        f'Upgrade realizado com sucesso! Seu plano foi alterado para {novo_plano.titulo}. '
        f'Todos os novos recursos já estão disponíveis.')
    
    return redirect('admin_loja:planos_meu_plano')

@painel_loja_required 
def atribuir_plano(request):
    """View para atribuir um plano específico ao lojista (uso administrativo/vendas)"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    # Esta view será usada pelo sistema de vendas para atribuir planos
    # Requer autenticação especial ou chave de API
    
    import json
    
    try:
        data = json.loads(request.body)
        restaurante_id = data.get('restaurante_id')
        plano_id = data.get('plano_id')
        dias_validade = data.get('dias_validade', 30)
        chave_api = data.get('api_key')
        
        # Verificar chave de API (implemente sua verificação de segurança aqui)
        # if chave_api != settings.VENDAS_API_KEY:
        #     return JsonResponse({'success': False, 'error': 'Chave de API inválida'})
        
        if not restaurante_id or not plano_id:
            return JsonResponse({'success': False, 'error': 'Dados obrigatórios faltando'})
        
        try:
            restaurante = Restaurante.objects.get(id=restaurante_id)
            plano = Plano.objects.get(id=plano_id, ativo=True)
        except (Restaurante.DoesNotExist, Plano.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Restaurante ou plano não encontrado'})
        
        # Atribuir o plano
        plano_anterior = restaurante.plano.titulo if restaurante.plano else "Nenhum"
        restaurante.plano = plano
        restaurante.data_vencimento_plano = timezone.now().date() + timedelta(days=dias_validade)
        restaurante.save()
        
        # Log da alteração
        print(f"PLANO ATRIBUÍDO VIA API: {restaurante.nome} - {plano_anterior} -> {plano.titulo}")
        
        return JsonResponse({
            'success': True,
            'message': f'Plano {plano.titulo} atribuído com sucesso ao restaurante {restaurante.nome}',
            'restaurante': restaurante.nome,
            'plano_anterior': plano_anterior,
            'plano_novo': plano.titulo,
            'data_vencimento': restaurante.data_vencimento_plano.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})

def listar_restaurantes_sem_plano(request):
    """API para listar restaurantes sem plano (para uso do sistema de vendas)"""
    
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Método não permitido'})
    
    # Verificar autenticação/API key aqui
    
    restaurantes_sem_plano = Restaurante.objects.filter(plano__isnull=True).values(
        'id', 'nome', 'email_contato', 'telefone', 'created_at'
    )
    
    return JsonResponse({
        'success': True,
        'restaurantes': list(restaurantes_sem_plano)
    })