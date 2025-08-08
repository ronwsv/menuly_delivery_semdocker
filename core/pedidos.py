from django.db import models
from django.utils import timezone
from .models import Usuario, Restaurante, Produto, ItemPersonalizacao, Endereco
import uuid


class Pedido(models.Model):
    """Modelo para pedidos"""
    STATUS_CHOICES = [
        ('carrinho', 'No Carrinho'),
        ('pendente', 'Pendente de Pagamento'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando'),
        ('pronto', 'Pronto'),
        ('saiu_entrega', 'Saiu para Entrega'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
        ('devolvido', 'Devolvido'),
    ]
    
    TIPO_ENTREGA_CHOICES = [
        ('delivery', 'Delivery'),
        ('retirada', 'Retirada no Local'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('cartao_debito', 'Cartão de Débito'),
        ('pix', 'PIX'),
        ('vale_refeicao', 'Vale Refeição'),
        ('online', 'Pagamento Online'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=20, unique=True, blank=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='pedidos')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pedidos', null=True, blank=True)
    
    # Dados do cliente (para guest checkout)
    cliente_nome = models.CharField(max_length=200)
    cliente_celular = models.CharField(max_length=15)
    cliente_email = models.EmailField(blank=True)
    
    # Endereço de entrega
    endereco_entrega = models.ForeignKey(Endereco, on_delete=models.SET_NULL, null=True, blank=True)
    endereco_cep = models.CharField(max_length=10, blank=True)
    endereco_logradouro = models.CharField(max_length=200, blank=True)
    endereco_numero = models.CharField(max_length=10, blank=True)
    endereco_complemento = models.CharField(max_length=100, blank=True)
    endereco_bairro = models.CharField(max_length=100, blank=True)
    endereco_cidade = models.CharField(max_length=100, blank=True)
    endereco_estado = models.CharField(max_length=2, blank=True)
    endereco_ponto_referencia = models.TextField(blank=True)
    
    # Configurações do pedido
    tipo_entrega = models.CharField(max_length=20, choices=TIPO_ENTREGA_CHOICES)
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES)
    troco_para = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Valores
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    taxa_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status e controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='carrinho')
    observacoes = models.TextField(blank=True)
    observacoes_internas = models.TextField(blank=True)
    
    # Datas
    data_agendamento = models.DateTimeField(null=True, blank=True)
    tempo_entrega_estimado = models.PositiveIntegerField(null=True, blank=True, help_text="Tempo em minutos")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_confirmacao = models.DateTimeField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar número sequencial do pedido
            ultimo_numero = Pedido.objects.filter(
                restaurante=self.restaurante
            ).exclude(
                status='carrinho'
            ).count() + 1
            self.numero = f"{ultimo_numero:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.numero} - {self.restaurante.nome}"

    def calcular_total(self):
        """Calcula o total do pedido"""
        self.subtotal = sum(item.subtotal for item in self.itens.all())
        self.total = self.subtotal + self.taxa_entrega - self.desconto
        self.save()

    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        if self.endereco_entrega:
            endereco = self.endereco_entrega
            return f"{endereco.logradouro}, {endereco.numero}"
        else:
            return f"{self.endereco_logradouro}, {self.endereco_numero}"

    @property
    def pode_cancelar(self):
        """Verifica se o pedido pode ser cancelado"""
        return self.status in ['pendente', 'confirmado']


class ItemPedido(models.Model):
    """Itens do pedido"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    
    # Dados do produto no momento do pedido (para histórico)
    produto_nome = models.CharField(max_length=200)
    produto_preco = models.DecimalField(max_digits=10, decimal_places=2)
    
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    observacoes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'itens_pedido'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def save(self, *args, **kwargs):
        if not self.produto_nome:
            self.produto_nome = self.produto.nome
        if not self.produto_preco:
            self.produto_preco = self.produto.preco_final
        if not self.preco_unitario:
            self.preco_unitario = self.produto.preco_final
        self.subtotal = self.preco_unitario * self.quantidade
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade}x {self.produto_nome}"


class PersonalizacaoItemPedido(models.Model):
    """Personalizações escolhidas para cada item do pedido"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item_pedido = models.ForeignKey(ItemPedido, on_delete=models.CASCADE, related_name='personalizacoes')
    item_personalizacao = models.ForeignKey(ItemPersonalizacao, on_delete=models.CASCADE)
    
    # Dados da personalização no momento do pedido
    opcao_nome = models.CharField(max_length=100)
    item_nome = models.CharField(max_length=100)
    preco_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'personalizacoes_item_pedido'
        verbose_name = 'Personalização do Item'
        verbose_name_plural = 'Personalizações dos Itens'

    def save(self, *args, **kwargs):
        if not self.opcao_nome:
            self.opcao_nome = self.item_personalizacao.opcao.nome
        if not self.item_nome:
            self.item_nome = self.item_personalizacao.nome
        if not self.preco_adicional:
            self.preco_adicional = self.item_personalizacao.preco_adicional
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.opcao_nome}: {self.item_nome}"


class HistoricoStatusPedido(models.Model):
    """Histórico de mudanças de status do pedido"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historico_status')
    status_anterior = models.CharField(max_length=20, choices=Pedido.STATUS_CHOICES, blank=True, null=True)
    status_novo = models.CharField(max_length=20, choices=Pedido.STATUS_CHOICES)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    observacoes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historico_status_pedido'
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Histórico de Status'
        ordering = ['timestamp']

    def __str__(self):
        return f"Pedido #{self.pedido.numero} - {self.status_anterior} → {self.status_novo}"


class AvaliacaoPedido(models.Model):
    """Avaliações dos pedidos pelos clientes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='avaliacao')
    nota_comida = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    nota_entrega = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    nota_geral = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'avaliacoes_pedido'
        verbose_name = 'Avaliação do Pedido'
        verbose_name_plural = 'Avaliações dos Pedidos'

    def __str__(self):
        return f"Avaliação - Pedido #{self.pedido.numero} - Nota {self.nota_geral}/5"
