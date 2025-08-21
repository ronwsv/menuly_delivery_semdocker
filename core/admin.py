from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Endereco, Plano, Restaurante, HorarioFuncionamento,
    Categoria, Produto, ImagemProduto, OpcaoPersonalizacao, ItemPersonalizacao,
    Pedido, ItemPedido, PersonalizacaoItemPedido, HistoricoStatusPedido, AvaliacaoPedido
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
    list_display = ('nome', 'proprietario', 'cidade', 'status', 'tipo_servico', 'esta_aberto')
    list_filter = ('status', 'tipo_servico', 'cidade', 'estado')
    search_fields = ('nome', 'proprietario__username', 'cidade')
    prepopulated_fields = {'slug': ('nome',)}
    inlines = [HorarioFuncionamentoInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'slug', 'descricao', 'proprietario', 'status')
        }),
        ('Mídia', {
            'fields': ('logo', 'banner', 'favicon', 'slogan')
        }),
        ('Contato', {
            'fields': ('telefone', 'whatsapp', 'email')
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado')
        }),
        ('Configurações Operacionais', {
            'fields': ('tipo_servico', 'taxa_entrega', 'valor_minimo_pedido', 'tempo_entrega_min', 'tempo_entrega_max')
        }),
        ('Personalização Visual', {
            'fields': ('cor_primaria', 'cor_secundaria', 'cor_destaque')
        }),
        ('Configurações de Pagamento', {
            'fields': ('aceita_agendamento', 'aceita_pagamento_online', 'aceita_pagamento_entrega')
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
