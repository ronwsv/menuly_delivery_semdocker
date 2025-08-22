from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.admin import SimpleListFilter
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from datetime import timedelta
from django import forms
from .models import (
    Usuario, Endereco, Plano, Restaurante, HorarioFuncionamento,
    Categoria, Produto, ImagemProduto, OpcaoPersonalizacao, ItemPersonalizacao,
    Pedido, ItemPedido, PersonalizacaoItemPedido, HistoricoStatusPedido, AvaliacaoPedido
)


class AtribuirPlanoForm(forms.Form):
    """Formulário para atribuir planos em massa"""
    
    plano = forms.ModelChoiceField(
        queryset=Plano.objects.filter(ativo=True),
        empty_label="Selecione um plano",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Escolha o plano que será atribuído aos restaurantes selecionados"
    )
    
    dias_validade = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Número de dias de validade do plano (1-365 dias)"
    )
    
    sobrescrever_plano_existente = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Marque para sobrescrever planos existentes, desmarque para aplicar apenas em restaurantes sem plano"
    )
    
    enviar_email_notificacao = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Enviar email de notificação para os proprietários dos restaurantes"
    )


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin para modelo Usuario customizado"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'celular', 'ativo')
    list_filter = ('tipo_usuario', 'ativo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'celular')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('tipo_usuario', 'celular', 'data_nascimento', 'cpf', 'avatar', 'ativo')
        }),
    )


class HorarioFuncionamentoInline(admin.TabularInline):
    model = HorarioFuncionamento
    extra = 7  # Para os 7 dias da semana


class PlanoFilter(SimpleListFilter):
    """Filtro personalizado para planos"""
    title = 'Status do Plano'
    parameter_name = 'plano_status'

    def lookups(self, request, model_admin):
        return (
            ('sem_plano', 'Sem plano'),
            ('plano_ativo', 'Com plano ativo'),
            ('plano_vencido', 'Plano vencido'),
            ('plano_prestes_vencer', 'Plano prestes a vencer (7 dias)'),
        )

    def queryset(self, request, queryset):
        hoje = timezone.now().date()
        
        if self.value() == 'sem_plano':
            return queryset.filter(plano__isnull=True)
        elif self.value() == 'plano_ativo':
            return queryset.filter(plano__isnull=False, data_vencimento_plano__gte=hoje)
        elif self.value() == 'plano_vencido':
            return queryset.filter(plano__isnull=False, data_vencimento_plano__lt=hoje)
        elif self.value() == 'plano_prestes_vencer':
            data_limite = hoje + timedelta(days=7)
            return queryset.filter(plano__isnull=False, data_vencimento_plano__gte=hoje, data_vencimento_plano__lte=data_limite)
        
        return queryset


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'nome', 'preco_mensal', 'preco_setup', 'destaque', 'ativo', 'ordem_exibicao')
    list_filter = ('ativo', 'destaque', 'nome')
    search_fields = ('titulo', 'descricao')
    ordering = ('ordem_exibicao', 'preco_mensal')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'titulo', 'descricao', 'ativo', 'destaque', 'ordem_exibicao')
        }),
        ('Preços', {
            'fields': ('preco_mensal', 'preco_setup')
        }),
        ('Limites', {
            'fields': ('limite_pedidos_mes', 'limite_produtos', 'limite_funcionarios', 'limite_lojas')
        }),
        ('Recursos', {
            'fields': (
                'permite_pagamento_online', 'permite_cupons_desconto', 'permite_whatsapp_bot',
                'permite_impressao_termica', 'permite_relatorios_avancados', 'permite_api_integracao',
                'permite_area_entregador', 'permite_multi_loja'
            )
        }),
    )


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'proprietario', 'plano_info', 'status_plano', 'cidade', 'status', 'esta_aberto')
    list_filter = ('status', 'tipo_servico', PlanoFilter, 'plano', 'cidade', 'estado')
    search_fields = ('nome', 'proprietario__username', 'cidade', 'plano__titulo')
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [HorarioFuncionamentoInline]
    actions = ['atribuir_plano_personalizado', 'atribuir_plano_starter', 'atribuir_plano_pro', 'renovar_plano_30_dias', 'remover_plano']
    
    def plano_info(self, obj):
        if obj.plano:
            return format_html(
                '<strong>{}</strong><br><small>R$ {}/mês</small>',
                obj.plano.titulo,
                obj.plano.preco_mensal
            )
        return format_html('<span style="color: #999;">Sem plano</span>')
    plano_info.short_description = 'Plano Atual'
    
    def status_plano(self, obj):
        if not obj.plano:
            return format_html('<span style="color: #dc3545;">❌ Sem plano</span>')
        
        hoje = timezone.now().date()
        if not obj.data_vencimento_plano:
            return format_html('<span style="color: #ffc107;">⚠️ Sem data vencimento</span>')
        
        dias_restantes = (obj.data_vencimento_plano - hoje).days
        
        if dias_restantes < 0:
            return format_html(
                '<span style="color: #dc3545;">🔴 Vencido há {} dias</span>',
                abs(dias_restantes)
            )
        elif dias_restantes <= 7:
            return format_html(
                '<span style="color: #ffc107;">🟡 Vence em {} dias</span>',
                dias_restantes
            )
        else:
            return format_html(
                '<span style="color: #28a745;">🟢 Válido por {} dias</span>',
                dias_restantes
            )
    status_plano.short_description = 'Status do Plano'
    
    # Actions personalizadas
    def atribuir_plano_personalizado(self, request, queryset):
        """Action para atribuir plano com formulário personalizado"""
        if 'apply' in request.POST:
            form = AtribuirPlanoForm(request.POST)
            if form.is_valid():
                plano = form.cleaned_data['plano']
                dias_validade = form.cleaned_data['dias_validade']
                sobrescrever = form.cleaned_data['sobrescrever_plano_existente']
                enviar_email = form.cleaned_data['enviar_email_notificacao']
                
                count = 0
                skipped = 0
                data_vencimento = timezone.now().date() + timedelta(days=dias_validade)
                
                for restaurante in queryset:
                    # Se não deve sobrescrever e já tem plano, pula
                    if not sobrescrever and restaurante.plano:
                        skipped += 1
                        continue
                    
                    plano_anterior = restaurante.plano.titulo if restaurante.plano else "Nenhum"
                    restaurante.plano = plano
                    restaurante.data_vencimento_plano = data_vencimento
                    restaurante.save()
                    
                    # Log da alteração
                    print(f"PLANO ATRIBUÍDO VIA ADMIN: {restaurante.nome} - {plano_anterior} -> {plano.titulo}")
                    
                    # TODO: Implementar envio de email se solicitado
                    if enviar_email:
                        pass  # Implementar notificação por email
                    
                    count += 1
                
                message = f'{count} restaurante(s) receberam o plano {plano.titulo} ({dias_validade} dias).'
                if skipped > 0:
                    message += f' {skipped} restaurante(s) foram ignorados (já possuem plano).'
                
                self.message_user(request, message)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = AtribuirPlanoForm()
        
        return render(request, 'admin/atribuir_plano.html', {
            'form': form,
            'restaurantes': queryset,
            'action_checkbox_name': admin.ACTION_CHECKBOX_NAME,
        })
    
    atribuir_plano_personalizado.short_description = "🎯 Atribuir plano personalizado"

    def atribuir_plano_starter(self, request, queryset):
        try:
            plano_starter = Plano.objects.get(nome='starter', ativo=True)
            count = 0
            for restaurante in queryset:
                restaurante.plano = plano_starter
                restaurante.data_vencimento_plano = timezone.now().date() + timedelta(days=30)
                restaurante.save()
                count += 1
            
            self.message_user(request, f'{count} restaurante(s) receberam o plano Starter (30 dias).')
        except Plano.DoesNotExist:
            self.message_user(request, 'Plano Starter não encontrado.', level='ERROR')
    atribuir_plano_starter.short_description = "🚀 Atribuir Plano Starter (30 dias)"
    
    def atribuir_plano_pro(self, request, queryset):
        try:
            plano_pro = Plano.objects.get(nome='pro', ativo=True)
            count = 0
            for restaurante in queryset:
                restaurante.plano = plano_pro
                restaurante.data_vencimento_plano = timezone.now().date() + timedelta(days=30)
                restaurante.save()
                count += 1
            
            self.message_user(request, f'{count} restaurante(s) receberam o plano Pro (30 dias).')
        except Plano.DoesNotExist:
            self.message_user(request, 'Plano Pro não encontrado.', level='ERROR')
    atribuir_plano_pro.short_description = "⭐ Atribuir Plano Pro (30 dias)"
    
    def renovar_plano_30_dias(self, request, queryset):
        count = 0
        for restaurante in queryset:
            if restaurante.plano:
                if restaurante.data_vencimento_plano and restaurante.data_vencimento_plano >= timezone.now().date():
                    # Se o plano ainda está válido, adiciona 30 dias
                    restaurante.data_vencimento_plano += timedelta(days=30)
                else:
                    # Se o plano está vencido, renova por 30 dias a partir de hoje
                    restaurante.data_vencimento_plano = timezone.now().date() + timedelta(days=30)
                restaurante.save()
                count += 1
        
        self.message_user(request, f'{count} restaurante(s) tiveram seus planos renovados por 30 dias.')
    renovar_plano_30_dias.short_description = "🔄 Renovar plano por 30 dias"
    
    def remover_plano(self, request, queryset):
        count = 0
        for restaurante in queryset:
            if restaurante.plano:
                restaurante.plano = None
                restaurante.data_vencimento_plano = None
                restaurante.save()
                count += 1
        
        self.message_user(request, f'{count} restaurante(s) tiveram seus planos removidos.')
    remover_plano.short_description = "❌ Remover plano"
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao', 'proprietario', 'status')
        }),
        ('Plano e Assinatura', {
            'fields': ('plano', 'data_vencimento_plano'),
            'classes': ('collapse',),
            'description': 'Gerencie o plano de assinatura do restaurante'
        }),
        ('Mídia', {
            'fields': ('logo', 'banner', 'favicon', 'slogan'),
            'classes': ('collapse',)
        }),
        ('Contato', {
            'fields': ('telefone', 'whatsapp', 'email'),
            'classes': ('collapse',)
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado'),
            'classes': ('collapse',)
        }),
        ('Configurações Operacionais', {
            'fields': ('tipo_servico', 'taxa_entrega', 'valor_minimo_pedido', 'tempo_entrega_min', 'tempo_entrega_max'),
            'classes': ('collapse',)
        }),
        ('Personalização Visual', {
            'fields': ('cor_primaria', 'cor_secundaria', 'cor_destaque'),
            'classes': ('collapse',)
        }),
        ('Configurações de Pagamento', {
            'fields': ('aceita_agendamento', 'aceita_pagamento_online', 'aceita_pagamento_entrega'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nome', 'cidade', 'bairro', 'principal')
    list_filter = ('cidade', 'estado', 'principal')
    search_fields = ('usuario__username', 'nome', 'logradouro', 'bairro', 'cidade')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'restaurante', 'ordem', 'ativo')
    list_filter = ('restaurante', 'ativo')
    search_fields = ('nome', 'restaurante__nome')
    prepopulated_fields = {'slug': ('nome',)}
    ordering = ('restaurante', 'ordem', 'nome')


class ImagemProdutoInline(admin.TabularInline):
    model = ImagemProduto
    extra = 1


class OpcaoPersonalizacaoInline(admin.StackedInline):
    model = OpcaoPersonalizacao
    extra = 0


class ItemPersonalizacaoInline(admin.TabularInline):
    model = ItemPersonalizacao
    extra = 1


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'restaurante', 'preco', 'preco_promocional', 'destaque', 'disponivel')
    list_filter = ('restaurante', 'categoria', 'destaque', 'disponivel')
    search_fields = ('nome', 'categoria__nome', 'restaurante__nome')
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [ImagemProdutoInline, OpcaoPersonalizacaoInline]
    ordering = ('restaurante', 'categoria', 'ordem', 'nome')


@admin.register(OpcaoPersonalizacao)
class OpcaoPersonalizacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'produto', 'tipo', 'obrigatorio', 'ordem', 'ativo')
    list_filter = ('tipo', 'obrigatorio', 'ativo')
    search_fields = ('nome', 'produto__nome')
    inlines = [ItemPersonalizacaoInline]


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('subtotal',)


class HistoricoStatusInline(admin.TabularInline):
    model = HistoricoStatusPedido
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'restaurante', 'cliente_nome', 'status', 'total', 'tipo_entrega', 'created_at')
    list_filter = ('status', 'tipo_entrega', 'forma_pagamento', 'restaurante', 'created_at')
    search_fields = ('numero', 'cliente_nome', 'cliente_celular', 'cliente_email')
    readonly_fields = ('numero', 'subtotal', 'total', 'created_at', 'updated_at')
    inlines = [ItemPedidoInline, HistoricoStatusInline]
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': ('numero', 'restaurante', 'status', 'created_at', 'updated_at')
        }),
        ('Cliente', {
            'fields': ('cliente', 'cliente_nome', 'cliente_celular', 'cliente_email')
        }),
        ('Entrega', {
            'fields': ('tipo_entrega', 'endereco_entrega', 'endereco_logradouro', 'endereco_numero', 
                      'endereco_complemento', 'endereco_bairro', 'endereco_cidade', 'endereco_estado',
                      'endereco_ponto_referencia')
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'troco_para')
        }),
        ('Valores', {
            'fields': ('subtotal', 'taxa_entrega', 'desconto', 'total')
        }),
        ('Observações', {
            'fields': ('observacoes', 'observacoes_internas')
        }),
        ('Datas', {
            'fields': ('data_agendamento', 'tempo_entrega_estimado', 'data_confirmacao', 'data_entrega')
        }),
    )


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'produto_nome', 'quantidade', 'preco_unitario', 'subtotal')
    list_filter = ('pedido__restaurante', 'pedido__status')
    search_fields = ('pedido__numero', 'produto_nome')


@admin.register(AvaliacaoPedido)
class AvaliacaoPedidoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'nota_geral', 'nota_comida', 'nota_entrega', 'created_at')
    list_filter = ('nota_geral', 'nota_comida', 'nota_entrega', 'created_at')
    search_fields = ('pedido__numero', 'comentario')
    readonly_fields = ('created_at',)
