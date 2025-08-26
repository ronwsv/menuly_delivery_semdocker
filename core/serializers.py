from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Pedido, Entregador, AceitePedido, AvaliacaoEntregador, 
    OcorrenciaEntrega, Restaurante, Produto, ItemPedido
)

User = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'celular', 'tipo_usuario']
        read_only_fields = ['id']


class EntregadorSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    status_display = serializers.ReadOnlyField()

    class Meta:
        model = Entregador
        fields = [
            'id', 'usuario', 'nome', 'telefone', 'cnh', 'veiculo', 
            'dados_bancarios', 'disponivel', 'em_pausa', 'nota_media', 
            'total_avaliacoes', 'total_entregas', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'nota_media', 'total_avaliacoes', 'total_entregas', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        # Permite que entregador altere seu próprio status de disponibilidade
        instance.disponivel = validated_data.get('disponivel', instance.disponivel)
        instance.em_pausa = validated_data.get('em_pausa', instance.em_pausa)
        instance.save()
        return instance


class RestauranteBasicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurante
        fields = ['id', 'nome', 'telefone', 'endereco_completo']
    
    endereco_completo = serializers.SerializerMethodField()
    
    def get_endereco_completo(self, obj):
        return f"{obj.logradouro}, {obj.numero}, {obj.bairro}, {obj.cidade}-{obj.estado}"


class ProdutoBasicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'preco_final']


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto = ProdutoBasicoSerializer(read_only=True)

    class Meta:
        model = ItemPedido
        fields = [
            'id', 'produto', 'produto_nome', 'quantidade', 
            'preco_unitario', 'subtotal', 'observacoes'
        ]


class PedidoSerializer(serializers.ModelSerializer):
    restaurante = RestauranteBasicoSerializer(read_only=True)
    entregador = EntregadorSerializer(read_only=True)
    itens = ItemPedidoSerializer(many=True, read_only=True)
    endereco_completo = serializers.ReadOnlyField()
    pode_cancelar = serializers.ReadOnlyField()

    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'restaurante', 'entregador', 'cliente_nome', 
            'cliente_celular', 'endereco_completo', 'tipo_entrega', 
            'forma_pagamento', 'subtotal', 'taxa_entrega', 'valor_entrega',
            'desconto', 'total', 'status', 'observacoes', 'observacoes_internas',
            'tempo_entrega_estimado', 'created_at', 'data_confirmacao', 
            'data_entrega', 'itens', 'pode_cancelar'
        ]
        read_only_fields = [
            'id', 'numero', 'subtotal', 'total', 'created_at', 
            'data_confirmacao', 'data_entrega'
        ]


class AceitePedidoSerializer(serializers.ModelSerializer):
    pedido = PedidoSerializer(read_only=True)
    entregador = EntregadorSerializer(read_only=True)

    class Meta:
        model = AceitePedido
        fields = ['id', 'pedido', 'entregador', 'data_aceite', 'status', 'observacoes']
        read_only_fields = ['id', 'data_aceite']


class AvaliacaoEntregadorSerializer(serializers.ModelSerializer):
    pedido_numero = serializers.CharField(source='pedido.numero', read_only=True)
    entregador_nome = serializers.CharField(source='entregador.nome', read_only=True)

    class Meta:
        model = AvaliacaoEntregador
        fields = [
            'id', 'pedido', 'pedido_numero', 'entregador', 'entregador_nome',
            'nota', 'comentario', 'data'
        ]
        read_only_fields = ['id', 'data']

    def validate_nota(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("A nota deve estar entre 1 e 5.")
        return value


class OcorrenciaEntregaSerializer(serializers.ModelSerializer):
    pedido_numero = serializers.CharField(source='pedido.numero', read_only=True)
    entregador_nome = serializers.CharField(source='entregador.nome', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = OcorrenciaEntrega
        fields = [
            'id', 'pedido', 'pedido_numero', 'entregador', 'entregador_nome',
            'tipo', 'tipo_display', 'descricao', 'data', 'resolvido', 
            'observacoes_resolucao'
        ]
        read_only_fields = ['id', 'data']


# Serializers específicos para actions

class AlterarStatusPedidoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Pedido.STATUS_CHOICES)
    observacoes = serializers.CharField(required=False, allow_blank=True)


class AtribuirEntregadorSerializer(serializers.Serializer):
    entregador_id = serializers.UUIDField()
    observacoes = serializers.CharField(required=False, allow_blank=True)


class RegistrarOcorrenciaSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=OcorrenciaEntrega.TIPO_CHOICES)
    descricao = serializers.CharField(max_length=1000)


class PedidosDisponiveisSerializer(serializers.ModelSerializer):
    """Serializer simplificado para pedidos disponíveis para entregadores"""
    restaurante_nome = serializers.CharField(source='restaurante.nome', read_only=True)
    endereco_resumo = serializers.SerializerMethodField()
    distancia_estimada = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'restaurante_nome', 'cliente_nome',
            'endereco_resumo', 'valor_entrega', 'total', 
            'tempo_entrega_estimado', 'created_at', 'distancia_estimada'
        ]

    def get_endereco_resumo(self, obj):
        return f"{obj.endereco_bairro}, {obj.endereco_cidade}"
    
    def get_distancia_estimada(self, obj):
        # Aqui você pode implementar cálculo de distância real
        # Por enquanto, retorna um valor estimado
        return "2.5 km"