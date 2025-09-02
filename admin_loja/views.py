from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django import forms
from django.utils import timezone
from .utils import painel_loja_required, verificar_permissao_gerencial, verificar_permissao_lojista, obter_restaurante_usuario
from .views_perfil import perfil_visualizar, perfil_editar, perfil_alterar_senha
from .views_suporte import suporte_index, suporte_contato, suporte_chat_api
from .views_planos import (planos_meu_plano, planos_comparar, planos_solicitar_upgrade, 
                          planos_historico_uso, planos_api_verificar_limite, processar_upgrade, 
                          atribuir_plano, listar_restaurantes_sem_plano)
from datetime import timedelta
from django.db.models import Sum, F
from django.db import models
from core.models import Pedido, ItemPedido


# ==================== VIEWS DE PERSONALIZAÇÃO AVANÇADA ====================

from .forms import (LogoForm, BannerForm, ImpressoraForm, CategoriaForm, ProdutoForm, 
                    PersonalizacaoVisulaForm, HorarioFuncionamentoFormSet, ContatoWhatsAppForm)

@login_required
def admin_loja_personalizar_loja(request):
    """View principal para personalização da loja"""
    from core.models import Restaurante, HorarioFuncionamento
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/personalizar_loja.html', {
            'msg': 'Você não tem permissão para personalizar esta loja.'
        })
    
    # Inicializar forms
    logo_form = LogoForm(instance=restaurante)
    banner_form = BannerForm(instance=restaurante)
    visual_form = PersonalizacaoVisulaForm(instance=restaurante)
    contato_form = ContatoWhatsAppForm(instance=restaurante)
    
    # Preparar horários existentes (criar se não existirem)
    horarios_existentes = []
    for dia in range(7):  # 0-6 para Seg-Dom
        horario, created = HorarioFuncionamento.objects.get_or_create(
            restaurante=restaurante,
            dia_semana=dia,
            defaults={
                'hora_abertura': '08:00',
                'hora_fechamento': '22:00',
                'ativo': True
            }
        )
        horarios_existentes.append(horario)
    
    horarios_formset = HorarioFuncionamentoFormSet(
        queryset=HorarioFuncionamento.objects.filter(
            restaurante=restaurante
        ).order_by('dia_semana')
    )
    
    msg = None
    msg_type = 'success'
    
    if request.method == 'POST':
        # Handle logo upload
        if 'logo' in request.FILES:
            logo_form = LogoForm(request.POST, request.FILES, instance=restaurante)
            if logo_form.is_valid():
                logo_form.save()
                msg = 'Logo atualizada com sucesso!'
        
        # Handle banner upload  
        elif 'banner' in request.FILES:
            banner_form = BannerForm(request.POST, request.FILES, instance=restaurante)
            if banner_form.is_valid():
                banner_form.save()
                msg = 'Banner atualizado com sucesso!'
        
        # Handle visual customization
        elif 'visual_form' in request.POST:
            visual_form = PersonalizacaoVisulaForm(
                request.POST, 
                request.FILES, 
                instance=restaurante
            )
            if visual_form.is_valid():
                visual_form.save()
                msg = 'Personalização visual salva com sucesso!'
        
        # Handle contact and WhatsApp
        elif 'contato_form' in request.POST:
            contato_form = ContatoWhatsAppForm(request.POST, instance=restaurante)
            if contato_form.is_valid():
                contato_form.save()
                msg = 'Informações de contato atualizadas com sucesso!'
            else:
                msg = 'Erro ao salvar informações de contato. Verifique os dados informados.'
                msg_type = 'error'
        
        # Handle business hours
        elif 'horarios_form' in request.POST:
            horarios_formset = HorarioFuncionamentoFormSet(
                request.POST,
                queryset=HorarioFuncionamento.objects.filter(
                    restaurante=restaurante
                ).order_by('dia_semana')
            )
            if horarios_formset.is_valid():
                instances = horarios_formset.save(commit=False)
                for instance in instances:
                    instance.restaurante = restaurante
                    instance.save()
                horarios_formset.save()
                msg = 'Horários de funcionamento atualizados com sucesso!'
            else:
                msg = 'Erro ao salvar horários. Verifique os dados informados.'
                msg_type = 'error'
    
    return render(request, 'admin_loja/personalizar_loja.html', {
        'restaurante': restaurante,
        'logo_form': logo_form,
        'banner_form': banner_form,
        'visual_form': visual_form,
        'contato_form': contato_form,
        'horarios_formset': horarios_formset,
        'msg': msg,
        'msg_type': msg_type,
        'logo_url': restaurante.logo.url if restaurante.logo else None,
        'banner_url': restaurante.banner.url if restaurante.banner else None,
        'favicon_url': restaurante.favicon.url if restaurante.favicon else None,
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
@painel_loja_required
def admin_loja_avancar_status_pedido(request, pedido_id):
    from core.models import Pedido
    
    # Buscar pedido baseado no tipo de usuário
    tipo_usuario = getattr(request.user, 'tipo_usuario', None)
    
    if tipo_usuario == 'lojista':
        pedido = Pedido.objects.get(id=pedido_id, restaurante__proprietario=request.user)
    else:
        # Gerente/Atendente: buscar pedidos dos restaurantes onde trabalha
        restaurantes = request.user.trabalha_em.all()
        pedido = Pedido.objects.get(id=pedido_id, restaurante__in=restaurantes)
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
            if user is not None and (
                (hasattr(user, 'tipo_usuario') and user.tipo_usuario in ['lojista', 'gerente'])
                or user.groups.filter(name='Atendente').exists()
            ):
                login(request, user)
                return redirect('admin_loja:dashboard')
            else:
                error = 'Usuário ou senha inválidos, ou você não tem permissão para acessar o painel.'
    else:
        form = AdminLojaLoginForm()
    return render(request, 'admin_loja/login.html', {'form': form, 'error': error})

@painel_loja_required
def admin_loja_dashboard(request):
    from core.models import Restaurante, Pedido, Produto, Notificacao
    from django.utils import timezone
    from datetime import timedelta, datetime
    
    # Buscar restaurante do usuário
    restaurante = obter_restaurante_usuario(request.user)
    
    context = {}
    
    if restaurante:
        # Dados do dashboard
        hoje = timezone.now().date()
        
        # Pedidos de hoje
        pedidos_hoje = Pedido.objects.filter(
            restaurante=restaurante,
            created_at__date=hoje
        ).exclude(status__in=['carrinho', 'cancelado'])
        
        # Novos pedidos (últimos 30 minutos)
        time_threshold = timezone.now() - timedelta(minutes=30)
        novos_pedidos = pedidos_hoje.filter(
            created_at__gte=time_threshold,
            status__in=['novo', 'confirmado']
        ).count()
        
        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.objects.filter(
            restaurante=restaurante,
            controlar_estoque=True,
            estoque_atual__lte=F('estoque_minimo')
        ).count()
        
        # Notificações não lidas
        notificacoes_nao_lidas = Notificacao.objects.filter(
            restaurante=restaurante,
            lida=False
        ).order_by('-created_at')[:10]
        
        # Estatísticas gerais
        total_pedidos_hoje = pedidos_hoje.count()
        total_vendas_hoje = pedidos_hoje.filter(
            status='finalizado'
        ).aggregate(
            total=models.Sum('total')
        )['total'] or 0
        
        context = {
            'restaurante': restaurante,
            'novos_pedidos': novos_pedidos,
            'produtos_estoque_baixo': produtos_estoque_baixo,
            'notificacoes_nao_lidas': notificacoes_nao_lidas,
            'total_pedidos_hoje': total_pedidos_hoje,
            'total_vendas_hoje': total_vendas_hoje,
        }
        
        # Verificar e criar notificações automáticas
        _verificar_estoque_baixo(restaurante)
        _verificar_novos_pedidos(restaurante)
    
    return render(request, 'admin_loja/dashboard.html', context)


def _verificar_estoque_baixo(restaurante):
    """Verifica produtos com estoque baixo e cria notificações se necessário"""
    from core.models import Produto, Notificacao
    from django.utils import timezone
    
    # Buscar produtos com estoque baixo
    produtos_estoque_baixo = Produto.objects.filter(
        restaurante=restaurante,
        controlar_estoque=True,
        estoque_atual__lte=F('estoque_minimo'),
        estoque_atual__gt=0
    )
    
    # Criar notificações para produtos que ainda não têm notificação recente
    for produto in produtos_estoque_baixo:
        # Verificar se já existe notificação recente (últimas 24 horas)
        notificacao_existente = Notificacao.objects.filter(
            restaurante=restaurante,
            produto=produto,
            tipo='estoque_baixo',
            created_at__gte=timezone.now() - timedelta(days=1)
        ).exists()
        
        if not notificacao_existente:
            Notificacao.objects.create(
                restaurante=restaurante,
                produto=produto,
                tipo='estoque_baixo',
                titulo=f'Estoque baixo: {produto.nome}',
                mensagem=f'O produto "{produto.nome}" está com estoque baixo. Restam apenas {produto.estoque_atual} unidades.',
                prioridade='alta',
                link_acao=f'/admin-loja/produtos/{produto.id}/editar/'
            )
    
    # Verificar produtos esgotados
    produtos_esgotados = Produto.objects.filter(
        restaurante=restaurante,
        controlar_estoque=True,
        estoque_atual=0
    )
    
    for produto in produtos_esgotados:
        notificacao_existente = Notificacao.objects.filter(
            restaurante=restaurante,
            produto=produto,
            tipo='estoque_esgotado',
            created_at__gte=timezone.now() - timedelta(days=1)
        ).exists()
        
        if not notificacao_existente:
            Notificacao.objects.create(
                restaurante=restaurante,
                produto=produto,
                tipo='estoque_esgotado',
                titulo=f'Produto esgotado: {produto.nome}',
                mensagem=f'O produto "{produto.nome}" está esgotado. Reponha o estoque o quanto antes.',
                prioridade='urgente',
                link_acao=f'/admin-loja/produtos/{produto.id}/editar/'
            )


def _verificar_novos_pedidos(restaurante):
    """Verifica novos pedidos e cria notificações"""
    from core.models import Pedido, Notificacao
    from django.utils import timezone
    
    # Buscar pedidos novos dos últimos 10 minutos que ainda não têm notificação
    time_threshold = timezone.now() - timedelta(minutes=10)
    pedidos_novos = Pedido.objects.filter(
        restaurante=restaurante,
        created_at__gte=time_threshold,
        status__in=['novo', 'confirmado']
    )
    
    for pedido in pedidos_novos:
        # Verificar se já existe notificação para este pedido
        notificacao_existente = Notificacao.objects.filter(
            restaurante=restaurante,
            pedido=pedido,
            tipo='pedido_novo'
        ).exists()
        
        if not notificacao_existente:
            Notificacao.objects.create(
                restaurante=restaurante,
                pedido=pedido,
                tipo='pedido_novo',
                titulo=f'Novo pedido #{pedido.numero}',
                mensagem=f'Pedido #{pedido.numero} recebido no valor de R$ {pedido.total}.',
                prioridade='alta',
                link_acao=f'/admin-loja/pedidos/'
            )


# ==================== VIEWS DE API PARA NOTIFICAÇÕES ====================

@login_required
def api_marcar_notificacao_lida(request, notificacao_id):
    """Marca uma notificação como lida"""
    from django.http import JsonResponse
    from core.models import Notificacao
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    try:
        notificacao = get_object_or_404(
            Notificacao, 
            id=notificacao_id, 
            restaurante__proprietario=request.user
        )
        
        notificacao.lida = True
        notificacao.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_verificar_notificacoes(request):
    """Verifica se há novas notificações"""
    from django.http import JsonResponse
    from core.models import Restaurante, Notificacao, Pedido, Produto
    from django.utils import timezone
    from datetime import timedelta
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return JsonResponse({'success': False, 'error': 'Restaurante não encontrado'})
    
    # Executar verificações de notificação
    _verificar_estoque_baixo(restaurante)
    _verificar_novos_pedidos(restaurante)
    
    # Buscar notificações recentes (últimos 2 minutos) que ainda não foram vistas
    time_threshold = timezone.now() - timedelta(minutes=2)
    novas_notificacoes = Notificacao.objects.filter(
        restaurante=restaurante,
        lida=False,
        created_at__gte=time_threshold
    ).order_by('-created_at')
    
    # Contadores atualizados
    contadores = {
        'notificacoes_nao_lidas': Notificacao.objects.filter(
            restaurante=restaurante, 
            lida=False
        ).count(),
        'novos_pedidos': Pedido.objects.filter(
            restaurante=restaurante,
            created_at__gte=timezone.now() - timedelta(minutes=30),
            status__in=['novo', 'confirmado']
        ).count(),
        'produtos_estoque_baixo': Produto.objects.filter(
            restaurante=restaurante,
            controlar_estoque=True,
            estoque_atual__lte=F('estoque_minimo')
        ).count(),
    }
    
    # Serializar notificações
    notificacoes_data = []
    for notificacao in novas_notificacoes:
        notificacoes_data.append({
            'id': str(notificacao.id),
            'titulo': notificacao.titulo,
            'mensagem': notificacao.mensagem,
            'tipo': notificacao.tipo,
            'prioridade': notificacao.prioridade,
            'icone': notificacao.icone,
            'cor': notificacao.cor,
            'link_acao': notificacao.link_acao,
            'created_at': notificacao.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'novas_notificacoes': notificacoes_data,
        'counters': contadores
    })


@login_required
def api_criar_notificacao_sistema(request):
    """Cria uma notificação do sistema (para testes)"""
    from django.http import JsonResponse
    from core.models import Restaurante, Notificacao
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método inválido'})
    
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return JsonResponse({'success': False, 'error': 'Restaurante não encontrado'})
    
    # Criar notificação de sistema de exemplo
    notificacao = Notificacao.objects.create(
        restaurante=restaurante,
        tipo='sistema',
        titulo='Sistema atualizado',
        mensagem='O sistema do painel foi atualizado com novas funcionalidades de notificação.',
        prioridade='media'
    )
    
    return JsonResponse({
        'success': True,
        'notificacao_id': str(notificacao.id)
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django import forms
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group

from core.models import Pedido, ItemPedido, Restaurante, Usuario, Categoria, Produto, Categoria, Produto, Categoria, Produto, Categoria, Produto, HorarioFuncionamento, Categoria, Produto, Categoria, Produto, HorarioFuncionamento, Categoria, Produto, Categoria, Produto, Categoria, Produto, Categoria, Produto, Categoria, Produto
from .models import Impressora
from .forms import (LogoForm, BannerForm, ImpressoraForm, CategoriaForm, ProdutoForm, 
                    PersonalizacaoVisulaForm, HorarioFuncionamentoFormSet, FuncionarioForm,
                    PerfilForm, AlterarSenhaForm)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'admin_loja/dashboard.html'
    login_url = 'admin_loja:login'


# ==================== VIEWS DE GESTÃO DE EQUIPE ====================

@painel_loja_required
def equipe_listar(request):
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/equipe_listar.html', {'msg': 'Restaurante não encontrado.'})
    
    funcionarios = restaurante.funcionarios.all().order_by('first_name')
    
    return render(request, 'admin_loja/equipe_listar.html', {
        'funcionarios': funcionarios,
        'restaurante': restaurante
    })

@painel_loja_required
def equipe_adicionar(request):
    restaurante = obter_restaurante_usuario(request.user)
    if not restaurante:
        return render(request, 'admin_loja/equipe_form.html', {'msg': 'Restaurante não encontrado.'})

    # Verificar limite do plano
    if not restaurante.pode_criar_funcionario():
        messages.error(request, 
            f'Limite de {restaurante.plano.limite_funcionarios} funcionários atingido. '
            f'Faça upgrade do seu plano para adicionar mais funcionários.')
        return redirect('admin_loja:equipe_listar')

    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            # Verificar novamente antes de salvar
            if not restaurante.pode_criar_funcionario():
                messages.error(request, 'Limite de funcionários atingido.')
                return redirect('admin_loja:equipe_listar')
                
            user = form.save(commit=False)
            user.username = user.email # Usar email como username
            user.save()
            restaurante.funcionarios.add(user)
            
            # Definir o tipo de usuário e grupo
            grupo_selecionado = form.cleaned_data.get('grupo')
            if grupo_selecionado:
                # Limpar grupos existentes e adicionar o novo
                user.groups.clear()
                user.groups.add(grupo_selecionado)
                
                if grupo_selecionado.name == 'Gerente':
                    user.tipo_usuario = 'gerente'
                elif grupo_selecionado.name == 'Atendente':
                    user.tipo_usuario = 'funcionario' # Mapeia Atendente para funcionario
                user.save()

            return redirect('admin_loja:equipe_listar')
    else:
        form = FuncionarioForm()
    
    return render(request, 'admin_loja/equipe_form.html', {
        'form': form,
        'titulo': 'Adicionar Funcionário',
        'restaurante': restaurante
    })

@painel_loja_required
def equipe_editar(request, user_id):
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/equipe_form.html', {'msg': 'Restaurante não encontrado.'})
    
    funcionario = get_object_or_404(Usuario, id=user_id)
    
    # Verificar se o funcionário pertence ao restaurante do lojista logado
    if funcionario not in restaurante.funcionarios.all():
        return render(request, 'admin_loja/equipe_form.html', {'msg': 'Funcionário não encontrado neste restaurante.'})

    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email # Garante que o username seja o email
            user.save()
            
            # Atualizar o tipo de usuário e grupo
            grupo_selecionado = form.cleaned_data.get('grupo')
            if grupo_selecionado:
                # Limpar grupos existentes e adicionar o novo
                user.groups.clear()
                user.groups.add(grupo_selecionado)
                
                if grupo_selecionado.name == 'Gerente':
                    user.tipo_usuario = 'gerente'
                elif grupo_selecionado.name == 'Atendente':
                    user.tipo_usuario = 'funcionario'
                user.save()

            return redirect('admin_loja:equipe_listar')
    else:
        form = FuncionarioForm(instance=funcionario)
    
    return render(request, 'admin_loja/equipe_form.html', {
        'form': form,
        'titulo': 'Editar Funcionário',
        'funcionario': funcionario,
        'restaurante': restaurante
    })

@painel_loja_required
def equipe_remover(request, user_id):
    restaurante = Restaurante.objects.filter(proprietario=request.user).first()
    if not restaurante:
        return render(request, 'admin_loja/equipe_listar.html', {'msg': 'Restaurante não encontrado.'})
    
    funcionario = get_object_or_404(Usuario, id=user_id)
    
    # Verificar se o funcionário pertence ao restaurante do lojista logado
    if funcionario not in restaurante.funcionarios.all():
        return render(request, 'admin_loja/equipe_listar.html', {'msg': 'Funcionário não encontrado neste restaurante.'})

    if request.method == 'POST':
        restaurante.funcionarios.remove(funcionario)
        # Opcional: Deletar o usuário se ele não estiver associado a nenhum outro restaurante
        # if not funcionario.trabalha_em.exists():
        #     funcionario.delete()
        return redirect('admin_loja:equipe_listar')
    
    return render(request, 'admin_loja/equipe_confirmar_remocao.html', {
        'funcionario': funcionario,
        'restaurante': restaurante
    })


# Página de pedidos do lojista
@painel_loja_required
def admin_loja_pedidos(request):
    # Buscar restaurantes baseado no tipo de usuário
    tipo_usuario = getattr(request.user, 'tipo_usuario', None)
    
    if tipo_usuario == 'lojista':
        # Lojista: buscar restaurantes que possui
        restaurantes = request.user.restaurantes.all()
    else:
        # Gerente/Atendente: buscar restaurantes onde trabalha
        restaurantes = request.user.trabalha_em.all()
    
    pedidos = []
    status_list = ['novo', 'preparo', 'pronto', 'entrega', 'finalizado']
    pedidos_por_status = {status: [] for status in status_list}
    
    if restaurantes.exists():
        pedidos = Pedido.objects.filter(restaurante__in=restaurantes).order_by('-created_at')
        for pedido in pedidos:
            if pedido.status in pedidos_por_status:
                pedidos_por_status[pedido.status].append(pedido)
    
    return render(request, 'admin_loja/pedidos.html', {'pedidos_por_status': pedidos_por_status})

@painel_loja_required
def admin_loja_relatorios(request):
    """Página de relatórios da loja - Apenas para Lojista e Gerente"""
    # Verificar permissão específica
    redirect_response = verificar_permissao_gerencial(request, "relatórios")
    if redirect_response:
        return redirect_response
        
    restaurante = obter_restaurante_usuario(request.user)
    if not restaurante:
        return render(request, 'admin_loja/relatorios.html', {'error': 'Restaurante não encontrado.'})
    
    # Verificar se o plano permite relatórios avançados
    relatorios_avancados = restaurante.tem_recurso('relatorios_avancados')

    # Vendas diárias
    hoje = timezone.now().date()
    vendas_hoje = Pedido.objects.filter(
        restaurante=restaurante,
        status='finalizado',
        created_at__date=hoje
    ).aggregate(total=Sum('total'))['total'] or 0

    # Vendas semanais
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    vendas_semana = Pedido.objects.filter(
        restaurante=restaurante,
        status='finalizado',
        created_at__date__range=[inicio_semana, fim_semana]
    ).aggregate(total=Sum('total'))['total'] or 0

    # Vendas mensais
    vendas_mes = Pedido.objects.filter(
        restaurante=restaurante,
        status='finalizado',
        created_at__year=hoje.year,
        created_at__month=hoje.month
    ).aggregate(total=Sum('total'))['total'] or 0

    # Dados para o gráfico de vendas dos últimos 7 dias
    vendas_ultimos_7_dias = []
    labels_ultimos_7_dias = []
    for i in range(7):
        dia = hoje - timedelta(days=i)
        total_dia = Pedido.objects.filter(
            restaurante=restaurante,
            status='finalizado',
            created_at__date=dia
        ).aggregate(total=Sum('total'))['total'] or 0
        vendas_ultimos_7_dias.insert(0, total_dia)
        labels_ultimos_7_dias.insert(0, dia.strftime('%d/%m'))

    # Produtos mais vendidos
    produtos_mais_vendidos = ItemPedido.objects.filter(
        pedido__restaurante=restaurante,
        pedido__status='finalizado'
    ).values('produto__nome').annotate(total_vendido=Sum('quantidade')).order_by('-total_vendido')[:10]

    # Recebimentos por forma de pagamento
    recebimentos_por_forma = Pedido.objects.filter(
        restaurante=restaurante,
        status='finalizado'
    ).values('forma_pagamento').annotate(total=Sum('total')).order_by('-total')

    context = {
        'vendas_hoje': vendas_hoje,
        'vendas_semana': vendas_semana,
        'vendas_mes': vendas_mes,
        'vendas_ultimos_7_dias': vendas_ultimos_7_dias,
        'labels_ultimos_7_dias': labels_ultimos_7_dias,
        'produtos_mais_vendidos': produtos_mais_vendidos,
        'recebimentos_por_forma': recebimentos_por_forma,
        'relatorios_avancados': relatorios_avancados,
        'restaurante': restaurante,
    }
    return render(request, 'admin_loja/relatorios.html', context)

# Visualização de cupom do pedido
@painel_loja_required
def admin_loja_cupom_pedido(request, pedido_id):
    # Buscar pedido baseado no tipo de usuário
    tipo_usuario = getattr(request.user, 'tipo_usuario', None)
    
    if tipo_usuario == 'lojista':
        pedido = get_object_or_404(Pedido, id=pedido_id, restaurante__proprietario=request.user)
        restaurante = pedido.restaurante
    else:
        # Gerente/Atendente: buscar pedidos dos restaurantes onde trabalha
        restaurantes = request.user.trabalha_em.all()
        pedido = get_object_or_404(Pedido, id=pedido_id, restaurante__in=restaurantes)
        restaurante = pedido.restaurante
    
    # Verificar se o plano permite cupons de desconto
    if not restaurante.tem_recurso('cupons_desconto'):
        messages.error(request, 'Cupons de desconto não disponíveis em seu plano. Faça upgrade para acessar este recurso.')
        return redirect('admin_loja:pedidos')
    
    itens = pedido.itens.all() if hasattr(pedido, 'itens') else []
    return render(request, 'admin_loja/cupom_pedido.html', {'pedido': pedido, 'itens': itens})


# ==================== VIEWS DE IMPRESSORAS ====================

@painel_loja_required
def admin_loja_impressoras(request):
    """Lista todas as impressoras do restaurante"""
    restaurante = obter_restaurante_usuario(request.user)
    if not restaurante:
        return render(request, 'admin_loja/impressoras.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    # Verificar se o plano permite impressão térmica
    if not restaurante.tem_recurso('impressao_termica'):
        messages.warning(request, 'Impressão térmica não disponível em seu plano. Faça upgrade para acessar este recurso.')
    
    impressoras = Impressora.objects.filter(restaurante=restaurante).order_by('-created_at')
    
    return render(request, 'admin_loja/impressoras.html', {
        'impressoras': impressoras,
        'restaurante': restaurante
    })

@painel_loja_required
def admin_loja_impressora_cadastrar(request):
    """Cadastrar nova impressora"""
    redirect_response = verificar_permissao_gerencial(request, "o gerenciamento de impressoras")
    if redirect_response:
        return redirect_response
        
    restaurante = obter_restaurante_usuario(request.user)
    if not restaurante:
        return render(request, 'admin_loja/impressora_form.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    # Verificar se o plano permite impressão térmica
    if not restaurante.tem_recurso('impressao_termica'):
        messages.error(request, 'Impressão térmica não disponível em seu plano. Faça upgrade para acessar este recurso.')
        return redirect('admin_loja:impressoras')
    
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

@painel_loja_required
def admin_loja_categorias(request):
    """Lista todas as categorias do restaurante - Apenas para Lojista e Gerente"""
    # Verificar permissão específica
    redirect_response = verificar_permissao_gerencial(request, "o gerenciamento de categorias")
    if redirect_response:
        return redirect_response
        
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

@painel_loja_required
def admin_loja_categoria_cadastrar(request):
    """Cadastrar nova categoria"""
    redirect_response = verificar_permissao_gerencial(request, "o gerenciamento de categorias")
    if redirect_response:
        return redirect_response
        
    restaurante = obter_restaurante_usuario(request.user)
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

@painel_loja_required
def admin_loja_produtos(request):
    """Lista todos os produtos do restaurante - Apenas para Lojista e Gerente"""
    # Verificar permissão específica
    redirect_response = verificar_permissao_gerencial(request, "o gerenciamento de produtos")
    if redirect_response:
        return redirect_response
        
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

@painel_loja_required
def admin_loja_produto_cadastrar(request):
    """Cadastrar novo produto"""
    redirect_response = verificar_permissao_gerencial(request, "o gerenciamento de produtos")
    if redirect_response:
        return redirect_response
        
    restaurante = obter_restaurante_usuario(request.user)
    if not restaurante:
        return render(request, 'admin_loja/produto_form.html', {
            'msg': 'Você não tem permissão para acessar esta página.'
        })
    
    # Verificar limite do plano
    if not restaurante.pode_criar_produto():
        messages.error(request, 
            f'Limite de {restaurante.plano.limite_produtos} produtos atingido. '
            f'Faça upgrade do seu plano para adicionar mais produtos.')
        return redirect('admin_loja:produtos')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, restaurante=restaurante)
        if form.is_valid():
            # Verificar novamente antes de salvar
            if not restaurante.pode_criar_produto():
                messages.error(request, 'Limite de produtos atingido.')
                return redirect('admin_loja:produtos')
                
            produto = form.save(commit=False)
            produto.restaurante = restaurante
            produto.save()
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('admin_loja:produtos')
    else:
        form = ProdutoForm(restaurante=restaurante)
    
    return render(request, 'admin_loja/produto_form.html', {
        'form': form,
        'titulo': 'Novo Produto',
        'restaurante': restaurante,
    })

@login_required
def admin_loja_produto_editar(request, produto_id):
    """Editar produto existente"""
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


@painel_loja_required
def admin_loja_produto_personalizar(request, produto_id):
    """View para gerenciar personalizações de um produto"""
    from core.models import Produto, OpcaoPersonalizacao, ItemPersonalizacao
    
    produto = get_object_or_404(
        Produto, 
        id=produto_id, 
        restaurante__proprietario=request.user
    )
    
    if request.method == 'POST':
        # Processar formulários de personalização
        action = request.POST.get('action')
        
        if action == 'adicionar_opcao':
            nome = request.POST.get('nome')
            tipo = request.POST.get('tipo', 'radio')
            obrigatorio = request.POST.get('obrigatorio') == 'on'
            quantidade_minima = int(request.POST.get('quantidade_minima', 0))
            quantidade_maxima = request.POST.get('quantidade_maxima')
            quantidade_maxima = int(quantidade_maxima) if quantidade_maxima else None
            
            if nome:
                # Determinar próxima ordem
                max_ordem = produto.opcoes_personalizacao.aggregate(
                    models.Max('ordem')
                )['ordem__max'] or 0
                
                OpcaoPersonalizacao.objects.create(
                    produto=produto,
                    nome=nome,
                    tipo=tipo,
                    obrigatorio=obrigatorio,
                    quantidade_minima=quantidade_minima,
                    quantidade_maxima=quantidade_maxima,
                    ordem=max_ordem + 1
                )
        
        elif action == 'editar_opcao':
            opcao_id = request.POST.get('opcao_id')
            nome = request.POST.get('nome')
            tipo = request.POST.get('tipo', 'radio')
            obrigatorio = request.POST.get('obrigatorio') == 'on'
            quantidade_minima = int(request.POST.get('quantidade_minima', 0))
            quantidade_maxima = request.POST.get('quantidade_maxima')
            quantidade_maxima = int(quantidade_maxima) if quantidade_maxima else None
            
            if opcao_id and nome:
                opcao = get_object_or_404(
                    OpcaoPersonalizacao,
                    id=opcao_id,
                    produto=produto
                )
                opcao.nome = nome
                opcao.tipo = tipo
                opcao.obrigatorio = obrigatorio
                opcao.quantidade_minima = quantidade_minima
                opcao.quantidade_maxima = quantidade_maxima
                opcao.save()
        
        elif action == 'deletar_opcao':
            opcao_id = request.POST.get('opcao_id')
            if opcao_id:
                OpcaoPersonalizacao.objects.filter(
                    id=opcao_id,
                    produto=produto
                ).delete()
        
        elif action == 'adicionar_item':
            opcao_id = request.POST.get('opcao_id')
            nome = request.POST.get('nome')
            preco_adicional = request.POST.get('preco_adicional', '0')
            
            if opcao_id and nome:
                opcao = get_object_or_404(
                    OpcaoPersonalizacao,
                    id=opcao_id,
                    produto=produto
                )
                
                # Determinar próxima ordem
                max_ordem = opcao.itens.aggregate(
                    models.Max('ordem')
                )['ordem__max'] or 0
                
                ItemPersonalizacao.objects.create(
                    opcao=opcao,
                    nome=nome,
                    preco_adicional=float(preco_adicional),
                    ordem=max_ordem + 1
                )
        
        elif action == 'editar_item':
            item_id = request.POST.get('item_id')
            nome = request.POST.get('nome')
            preco_adicional = request.POST.get('preco_adicional', '0')
            
            if item_id and nome:
                item = get_object_or_404(
                    ItemPersonalizacao,
                    id=item_id,
                    opcao__produto=produto
                )
                item.nome = nome
                item.preco_adicional = float(preco_adicional)
                item.save()
        
        elif action == 'deletar_item':
            item_id = request.POST.get('item_id')
            if item_id:
                ItemPersonalizacao.objects.filter(
                    id=item_id,
                    opcao__produto=produto
                ).delete()
        
        return redirect('admin_loja:produto_personalizar', produto_id=produto.id)
    
    # Buscar opções de personalização existentes
    opcoes_personalizacao = produto.opcoes_personalizacao.all().prefetch_related('itens')
    
    return render(request, 'admin_loja/produto_personalizar.html', {
        'produto': produto,
        'opcoes_personalizacao': opcoes_personalizacao,
    })

