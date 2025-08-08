from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils import timezone
import uuid


class Usuario(AbstractUser):
    """Modelo customizado de usuário para o sistema multi-site"""
    TIPO_USUARIO_CHOICES = [
        ('cliente', 'Cliente'),
        ('funcionario', 'Funcionário'),
        ('gerente', 'Gerente'),
        ('lojista', 'Lojista'),
        ('superadmin', 'Super Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='cliente')
    celular = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Número de telefone deve estar no formato: '+999999999'. Até 15 dígitos permitidos."
        )]
    )
    data_nascimento = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_tipo_usuario_display()})"


class Endereco(models.Model):
    """Modelo para endereços dos usuários"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='enderecos')
    nome = models.CharField(max_length=100, help_text="Ex: Casa, Trabalho, etc.")
    cep = models.CharField(max_length=10)
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    ponto_referencia = models.TextField(blank=True)
    principal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enderecos'
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        return f"{self.nome} - {self.logradouro}, {self.numero}"


class Restaurante(models.Model):
    """Modelo para restaurantes (lojas)"""
    TIPO_SERVICO_CHOICES = [
        ('delivery', 'Delivery'),
        ('balcao', 'Balcão'),
        ('ambos', 'Delivery + Balcão'),
    ]
    
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('manutencao', 'Em Manutenção'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    descricao = models.TextField()
    logo = models.ImageField(upload_to='restaurantes/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='restaurantes/banners/', null=True, blank=True)
    favicon = models.ImageField(upload_to='restaurantes/favicons/', null=True, blank=True)
    slogan = models.CharField(max_length=200, blank=True)
    
    # Informações de contato
    telefone = models.CharField(max_length=15)
    whatsapp = models.CharField(max_length=15, blank=True)
    email = models.EmailField()
    
    # Endereço
    cep = models.CharField(max_length=10)
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    # Configurações operacionais
    tipo_servico = models.CharField(max_length=20, choices=TIPO_SERVICO_CHOICES, default='ambos')
    taxa_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    valor_minimo_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tempo_entrega_min = models.PositiveIntegerField(default=30, help_text="Tempo em minutos")
    tempo_entrega_max = models.PositiveIntegerField(default=60, help_text="Tempo em minutos")
    
    # Personalização visual (White Label)
    cor_primaria = models.CharField(max_length=7, default='#dc3545', help_text="Cor primária em hex")
    cor_secundaria = models.CharField(max_length=7, default='#6c757d', help_text="Cor secundária em hex")
    cor_destaque = models.CharField(max_length=7, default='#ffc107', help_text="Cor de destaque em hex")
    
    # Configurações
    aceita_agendamento = models.BooleanField(default=False)
    aceita_pagamento_online = models.BooleanField(default=True)
    aceita_pagamento_entrega = models.BooleanField(default=True)
    
    # Status e gestão
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo')
    proprietario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='restaurantes')
    funcionarios = models.ManyToManyField(Usuario, related_name='trabalha_em', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurantes'
        verbose_name = 'Restaurante'
        verbose_name_plural = 'Restaurantes'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    @property
    def esta_aberto(self):
        """Verifica se o restaurante está aberto com base no horário"""
        # TODO: Implementar lógica de horário de funcionamento
        return self.status == 'ativo'


class HorarioFuncionamento(models.Model):
    """Horários de funcionamento do restaurante"""
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_abertura = models.TimeField()
    hora_fechamento = models.TimeField()
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'horarios_funcionamento'
        verbose_name = 'Horário de Funcionamento'
        verbose_name_plural = 'Horários de Funcionamento'
        unique_together = ['restaurante', 'dia_semana']

    def __str__(self):
        return f"{self.restaurante.nome} - {self.get_dia_semana_display()}: {self.hora_abertura} às {self.hora_fechamento}"


class Categoria(models.Model):
    """Categorias de produtos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    descricao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to='categorias/', null=True, blank=True)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['ordem', 'nome']
        unique_together = ['restaurante', 'slug']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.restaurante.nome} - {self.nome}"


class Produto(models.Model):
    """Produtos do cardápio"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='produtos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    preco_promocional = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Imagens
    imagem_principal = models.ImageField(upload_to='produtos/', null=True, blank=True)
    
    # Configurações
    destaque = models.BooleanField(default=False, help_text="Produto em destaque na página inicial")
    disponivel = models.BooleanField(default=True)
    permite_observacoes = models.BooleanField(default=True)
    tempo_preparo = models.PositiveIntegerField(default=15, help_text="Tempo em minutos")
    
    # Informações nutricionais/extras
    calorias = models.PositiveIntegerField(null=True, blank=True)
    ingredientes = models.TextField(blank=True)
    alergicos = models.TextField(blank=True, help_text="Informações sobre alérgenos")
    
    # Controle
    ordem = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['ordem', 'nome']
        unique_together = ['restaurante', 'slug']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.restaurante.nome} - {self.nome}"

    @property
    def preco_final(self):
        """Retorna o preço promocional se disponível, caso contrário o preço normal"""
        return self.preco_promocional if self.preco_promocional else self.preco

    @property
    def tem_promocao(self):
        """Verifica se o produto está em promoção"""
        return bool(self.preco_promocional and self.preco_promocional < self.preco)


class ImagemProduto(models.Model):
    """Imagens adicionais dos produtos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='produtos/galeria/')
    ordem = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'imagens_produtos'
        verbose_name = 'Imagem do Produto'
        verbose_name_plural = 'Imagens dos Produtos'
        ordering = ['ordem']

    def __str__(self):
        return f"Imagem {self.ordem} - {self.produto.nome}"


class OpcaoPersonalizacao(models.Model):
    """Opções de personalização dos produtos (ex: tamanho, sabor, etc.)"""
    TIPO_CHOICES = [
        ('radio', 'Seleção Única'),
        ('checkbox', 'Múltipla Escolha'),
        ('select', 'Lista Suspensa'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='opcoes_personalizacao')
    nome = models.CharField(max_length=100, help_text="Ex: Tamanho, Sabor, Adicionais")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='radio')
    obrigatorio = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'opcoes_personalizacao'
        verbose_name = 'Opção de Personalização'
        verbose_name_plural = 'Opções de Personalização'
        ordering = ['ordem']

    def __str__(self):
        return f"{self.produto.nome} - {self.nome}"


class ItemPersonalizacao(models.Model):
    """Itens das opções de personalização"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opcao = models.ForeignKey(OpcaoPersonalizacao, on_delete=models.CASCADE, related_name='itens')
    nome = models.CharField(max_length=100)
    preco_adicional = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'itens_personalizacao'
        verbose_name = 'Item de Personalização'
        verbose_name_plural = 'Itens de Personalização'
        ordering = ['ordem']

    def __str__(self):
        return f"{self.opcao.nome} - {self.nome}"


# ====================== MODELOS DE PEDIDOS ======================

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
            # Gerar número com iniciais do restaurante + número sequencial
            initials = ''.join([word[0].upper() for word in self.restaurante.nome.split()[:2]])
            ultimo_numero = Pedido.objects.filter(
                restaurante=self.restaurante
            ).exclude(
                status='carrinho'
            ).count() + 1
            
            # Formato: XX000001# (iniciais + 6 dígitos + #)
            import time
            timestamp_suffix = str(int(time.time()))[-3:]  # últimos 3 dígitos do timestamp
            self.numero = f"{initials}{ultimo_numero:03d}{timestamp_suffix}#"
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
