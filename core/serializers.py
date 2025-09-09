"""
Serializers para APIs do sistema Menuly.
Padroniza a serialização de dados para APIs REST.
"""

from rest_framework import serializers
from decimal import Decimal
from typing import Dict, Any

from .models import (
    Produto, Categoria, Restaurante, Pedido, ItemPedido,
    Carrinho, CarrinhoItem, Usuario, Endereco,
    OpcaoPersonalizacao, ItemPersonalizacao,
    Entregador, AceitePedido, AvaliacaoEntregador, OcorrenciaEntrega
)
from .validators import (
    CarrinhoValidators, PedidoValidators, ValidadorEcommerce,
    ValidadorCEP
)


class RestauranteBasicoSerializer(serializers.ModelSerializer):
    """Serializer básico para dados do restaurante"""
    
    class Meta:
        model = Restaurante
        fields = [
            'id', 'nome', 'slug', 'logo', 'slogan', 
            'telefone', 'whatsapp', 'status', 'esta_aberto'
        ]


class CategoriaSerializer(serializers.ModelSerializer):
    """Serializer para categorias de produtos"""
    
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'slug', 'descricao', 'imagem', 'ordem']


class ItemPersonalizacaoSerializer(serializers.ModelSerializer):
    """Serializer para itens de personalização"""
    
    class Meta:
        model = ItemPersonalizacao
        fields = ['id', 'nome', 'preco_adicional', 'ordem']


class OpcaoPersonalizacaoSerializer(serializers.ModelSerializer):
    """Serializer para opções de personalização"""
    itens = ItemPersonalizacaoSerializer(many=True, read_only=True)
    
    class Meta:
        model = OpcaoPersonalizacao
        fields = [
            'id', 'nome', 'tipo', 'obrigatorio', 
            'quantidade_minima', 'quantidade_maxima', 'itens'
        ]


class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer completo para produtos"""
    categoria = CategoriaSerializer(read_only=True)
    opcoes_personalizacao = OpcaoPersonalizacaoSerializer(many=True, read_only=True)
    preco_final = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tem_promocao = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'slug', 'descricao', 'preco', 'preco_promocional',
            'preco_final', 'tem_promocao', 'imagem_principal', 'destaque',
            'disponivel', 'permite_observacoes', 'permite_meio_a_meio',
            'tempo_preparo', 'estoque_atual', 'estoque_baixo', 'estoque_esgotado',
            'categoria', 'opcoes_personalizacao'
        ]


class ProdutoBasicoSerializer(serializers.ModelSerializer):
    """Serializer básico para produtos (para listagens)"""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    preco_final = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'preco', 'preco_final', 'imagem_principal',
            'disponivel', 'categoria_nome', 'permite_meio_a_meio'
        ]


class CarrinhoItemSerializer(serializers.ModelSerializer):
    """Serializer para itens do carrinho"""
    produto = ProdutoBasicoSerializer(read_only=True)
    produto_id = serializers.UUIDField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    eh_meio_a_meio = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CarrinhoItem
        fields = [
            'id', 'produto', 'produto_id', 'quantidade', 'preco_unitario',
            'subtotal', 'observacoes', 'dados_personalizacao', 'eh_meio_a_meio'
        ]
        read_only_fields = ['id', 'preco_unitario', 'subtotal']
    
    def validate_quantidade(self, value):
        CarrinhoValidators.validar_quantidade(value)
        return value
    
    def validate_produto_id(self, value):
        try:
            produto = Produto.objects.get(id=value)
            CarrinhoValidators.validar_produto_disponivel(produto)
            return value
        except Produto.DoesNotExist:
            raise serializers.ValidationError("Produto não encontrado")
    
    def validate(self, attrs):
        produto_id = attrs.get('produto_id')
        quantidade = attrs.get('quantidade', 1)
        personalizacoes = attrs.get('dados_personalizacao', {}).get('personalizacoes', [])
        meio_a_meio = attrs.get('dados_personalizacao', {}).get('meio_a_meio')
        
        if produto_id:
            try:
                produto = Produto.objects.get(id=produto_id)
                CarrinhoValidators.validar_estoque(produto, quantidade)
                CarrinhoValidators.validar_personalizacoes(personalizacoes, produto)
                if meio_a_meio:
                    CarrinhoValidators.validar_meio_a_meio(meio_a_meio, produto)
            except Produto.DoesNotExist:
                pass  # Já validado em validate_produto_id
        
        return attrs


class CarrinhoSerializer(serializers.ModelSerializer):
    """Serializer para carrinho completo"""
    itens = CarrinhoItemSerializer(many=True, read_only=True)
    total_itens = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Carrinho
        fields = ['id', 'itens', 'total_itens', 'subtotal', 'updated_at']


class AdicionarItemCarrinhoSerializer(serializers.Serializer):
    """Serializer para adicionar item ao carrinho"""
    produto_id = serializers.CharField()  # Mudou de UUIDField para CharField para aceitar IDs meio-a-meio
    quantidade = serializers.IntegerField(default=1)
    observacoes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    personalizacoes = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )
    dados_meio_a_meio = serializers.DictField(required=False, allow_null=True)
    meio_a_meio = serializers.DictField(required=False, allow_null=True)  # Campo adicional para dados meio-a-meio
    nome = serializers.CharField(required=False, allow_blank=True)  # Nome customizado para meio-a-meio
    preco_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)  # Preço customizado
    
    def validate_quantidade(self, value):
        CarrinhoValidators.validar_quantidade(value)
        return value
    
    def validate_produto_id(self, value):
        # Verificar se é um ID de meio-a-meio (formato: meio-uuid-uuid)
        if str(value).startswith('meio-'):
            # Para meio-a-meio, não validamos o produto agora, será validado na view
            return value
        
        # Para produtos normais, validar se existe
        try:
            from uuid import UUID
            UUID(str(value))  # Verificar se é um UUID válido
            produto = Produto.objects.get(id=value)
            CarrinhoValidators.validar_produto_disponivel(produto)
            return value
        except (ValueError, Produto.DoesNotExist):
            raise serializers.ValidationError("Deve ser um UUID válido.")
    
    def validate_observacoes(self, value):
        from .validators import ValidadorEcommerce
        return ValidadorEcommerce.sanitizar_observacoes(value or "")


class EnderecoSerializer(serializers.ModelSerializer):
    """Serializer para endereços"""
    
    class Meta:
        model = Endereco
        fields = [
            'id', 'nome', 'cep', 'logradouro', 'numero', 'complemento',
            'bairro', 'cidade', 'estado', 'ponto_referencia', 'principal'
        ]
    
    def validate_cep(self, value):
        return ValidadorCEP.validar_formato_cep(value)


class DadosClienteSerializer(serializers.Serializer):
    """Serializer para dados do cliente no checkout"""
    nome = serializers.CharField(max_length=200)
    celular = serializers.CharField(max_length=15)
    email = serializers.EmailField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        PedidoValidators.validar_dados_cliente(attrs)
        return attrs


class DadosEntregaSerializer(serializers.Serializer):
    """Serializer para dados de entrega"""
    tipo = serializers.ChoiceField(choices=['delivery', 'retirada'])
    cep = serializers.CharField(max_length=10, required=False)
    logradouro = serializers.CharField(max_length=200, required=False)
    numero = serializers.CharField(max_length=10, required=False)
    complemento = serializers.CharField(max_length=100, required=False, allow_blank=True)
    bairro = serializers.CharField(max_length=100, required=False)
    cidade = serializers.CharField(max_length=100, required=False)
    estado = serializers.CharField(max_length=2, required=False)
    ponto_referencia = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, attrs):
        PedidoValidators.validar_tipo_entrega(attrs['tipo'])
        
        if attrs['tipo'] == 'delivery':
            PedidoValidators.validar_endereco_entrega(attrs)
        
        return attrs


class CriarPedidoSerializer(serializers.Serializer):
    """Serializer para criar pedido do carrinho"""
    dados_cliente = DadosClienteSerializer()
    dados_entrega = DadosEntregaSerializer()
    forma_pagamento = serializers.ChoiceField(
        choices=['dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'vale_refeicao']
    )
    troco_para = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    observacoes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_troco_para(self, value):
        if value is not None:
            return ValidadorEcommerce.validar_preco(value)
        return value
    
    def validate_observacoes(self, value):
        from .validators import ValidadorEcommerce
        return ValidadorEcommerce.sanitizar_observacoes(value or "")
    
    def validate(self, attrs):
        forma_pagamento = attrs['forma_pagamento']
        troco_para = attrs.get('troco_para')
        
        PedidoValidators.validar_forma_pagamento(forma_pagamento, troco_para)
        
        return attrs


class ItemPedidoSerializer(serializers.ModelSerializer):
    """Serializer para itens do pedido"""
    produto_categoria = serializers.CharField(source='produto.categoria.nome', read_only=True)
    
    class Meta:
        model = ItemPedido
        fields = [
            'id', 'produto_nome', 'produto_categoria', 'quantidade',
            'preco_unitario', 'subtotal', 'observacoes', 'meio_a_meio'
        ]


class PedidoSerializer(serializers.ModelSerializer):
    """Serializer para pedidos"""
    itens = ItemPedidoSerializer(many=True, read_only=True)
    restaurante = RestauranteBasicoSerializer(read_only=True)
    endereco_completo = serializers.CharField(read_only=True)
    pode_cancelar = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'restaurante', 'cliente_nome', 'cliente_celular',
            'tipo_entrega', 'forma_pagamento', 'subtotal', 'taxa_entrega',
            'total', 'status', 'observacoes', 'endereco_completo',
            'created_at', 'pode_cancelar', 'itens'
        ]


class PedidoBasicoSerializer(serializers.ModelSerializer):
    """Serializer básico para listagem de pedidos"""
    restaurante_nome = serializers.CharField(source='restaurante.nome', read_only=True)
    total_itens = serializers.SerializerMethodField()
    
    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'restaurante_nome', 'total', 'status',
            'created_at', 'total_itens'
        ]
    
    def get_total_itens(self, obj):
        return sum(item.quantidade for item in obj.itens.all())


class CalcularFreteSerializer(serializers.Serializer):
    """Serializer para calcular frete"""
    cep = serializers.CharField(max_length=10)
    
    def validate_cep(self, value):
        return ValidadorCEP.validar_formato_cep(value)


class FreteResponseSerializer(serializers.Serializer):
    """Serializer para resposta de cálculo de frete"""
    valor_frete = serializers.DecimalField(max_digits=8, decimal_places=2)
    tempo_estimado_min = serializers.IntegerField()
    tempo_estimado_max = serializers.IntegerField()
    area_entrega_valida = serializers.BooleanField()
    distancia_km = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)


class ErroAPISerializer(serializers.Serializer):
    """Serializer padronizado para erros da API"""
    erro = serializers.CharField()
    detalhes = serializers.DictField(required=False)
    codigo = serializers.CharField(required=False)


class SucessoAPISerializer(serializers.Serializer):
    """Serializer padronizado para sucesso da API"""
    sucesso = serializers.BooleanField(default=True)
    mensagem = serializers.CharField()
    dados = serializers.DictField(required=False)


# ======================= SERIALIZERS PARA ENTREGADORES =======================

class EntregadorSerializer(serializers.ModelSerializer):
    """Serializer para entregadores"""
    status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Entregador
        fields = [
            'id', 'nome', 'telefone', 'cnh', 'veiculo', 
            'disponivel', 'em_pausa', 'nota_media', 'total_avaliacoes',
            'total_entregas', 'status_display'
        ]
        read_only_fields = ['nota_media', 'total_avaliacoes', 'total_entregas']


class AceitePedidoSerializer(serializers.ModelSerializer):
    """Serializer para aceite de pedidos"""
    entregador_nome = serializers.CharField(source='entregador.nome', read_only=True)
    pedido_numero = serializers.CharField(source='pedido.numero', read_only=True)
    
    class Meta:
        model = AceitePedido
        fields = [
            'id', 'pedido', 'entregador', 'pedido_numero', 'entregador_nome',
            'data_aceite', 'status', 'observacoes'
        ]


class AvaliacaoEntregadorSerializer(serializers.ModelSerializer):
    """Serializer para avaliações de entregadores"""
    entregador_nome = serializers.CharField(source='entregador.nome', read_only=True)
    pedido_numero = serializers.CharField(source='pedido.numero', read_only=True)
    
    class Meta:
        model = AvaliacaoEntregador
        fields = [
            'id', 'pedido', 'entregador', 'pedido_numero', 'entregador_nome',
            'nota', 'comentario', 'data'
        ]
    
    def validate_nota(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Nota deve estar entre 1 e 5")
        return value


class OcorrenciaEntregaSerializer(serializers.ModelSerializer):
    """Serializer para ocorrências de entrega"""
    entregador_nome = serializers.CharField(source='entregador.nome', read_only=True)
    pedido_numero = serializers.CharField(source='pedido.numero', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = OcorrenciaEntrega
        fields = [
            'id', 'pedido', 'entregador', 'pedido_numero', 'entregador_nome',
            'tipo', 'tipo_display', 'descricao', 'data', 'resolvido', 
            'observacoes_resolucao'
        ]


# ======================= SERIALIZERS PARA AÇÕES DA API =======================

class AlterarStatusPedidoSerializer(serializers.Serializer):
    """Serializer para alterar status do pedido"""
    status = serializers.ChoiceField(choices=Pedido.STATUS_CHOICES)
    observacoes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_observacoes(self, value):
        from .validators import ValidadorEcommerce
        return ValidadorEcommerce.sanitizar_observacoes(value or "")


class AtribuirEntregadorSerializer(serializers.Serializer):
    """Serializer para atribuir entregador ao pedido"""
    entregador_id = serializers.UUIDField()
    observacoes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_entregador_id(self, value):
        try:
            entregador = Entregador.objects.get(id=value)
            if not entregador.disponivel or entregador.em_pausa:
                raise serializers.ValidationError("Entregador não está disponível")
            return value
        except Entregador.DoesNotExist:
            raise serializers.ValidationError("Entregador não encontrado")


class RegistrarOcorrenciaSerializer(serializers.Serializer):
    """Serializer para registrar ocorrência de entrega"""
    tipo = serializers.ChoiceField(choices=OcorrenciaEntrega.TIPO_CHOICES)
    descricao = serializers.CharField(max_length=1000)
    
    def validate_descricao(self, value):
        from .validators import ValidadorEcommerce
        return ValidadorEcommerce.sanitizar_observacoes(value)


class PedidosDisponiveisSerializer(serializers.Serializer):
    """Serializer para filtrar pedidos disponíveis para entrega"""
    raio_km = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    apenas_sem_entregador = serializers.BooleanField(default=True)
    
    def validate_raio_km(self, value):
        if value and (value <= 0 or value > 50):
            raise serializers.ValidationError("Raio deve estar entre 0.1 e 50 km")
        return value