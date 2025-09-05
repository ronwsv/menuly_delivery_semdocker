def calcular_distancia_entre_ceps(cep_origem, cep_destino, api_url='http://localhost:5000/calcular-frete'):
    """
    Calcula a distância entre dois CEPs usando o utilitário local (OpenCage/ViaCEP).
    Retorna a distância em km (float) ou None em caso de erro.
    """
    from core.utils_frete_cep import calcular_frete_cep
    resultado = calcular_frete_cep(cep_destino=cep_destino, cep_referencia=cep_origem)
    if resultado and 'distancia_km' in resultado:
        return resultado['distancia_km']
    return None
from django.db import models
# Relacionamento entre Restaurante e Cliente
class RestauranteCliente(models.Model):
    restaurante = models.ForeignKey('Restaurante', on_delete=models.CASCADE, related_name='clientes')
    cliente = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='restaurantes_cliente')
    criado_em = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('restaurante', 'cliente')
        verbose_name = 'Cliente do Restaurante'
        verbose_name_plural = 'Clientes do Restaurante'
    def __str__(self):
        return f"{self.cliente} em {self.restaurante}"
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
        ('entregador', 'Entregador'),
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


class Plano(models.Model):
    """Modelo para planos de assinatura dos lojistas"""
    NOME_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('multi', 'Multi-Loja'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=20, choices=NOME_CHOICES, unique=True)
    titulo = models.CharField(max_length=100, help_text='Título exibido para o usuário')
    descricao = models.TextField()
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2)
    preco_setup = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text='Taxa de configuração inicial')
    
    # Limites do plano
    limite_pedidos_mes = models.PositiveIntegerField(null=True, blank=True, help_text='Null = ilimitado')
    limite_produtos = models.PositiveIntegerField(null=True, blank=True, help_text='Null = ilimitado')
    limite_funcionarios = models.PositiveIntegerField(default=1)
    limite_lojas = models.PositiveIntegerField(default=1)
    
    # Recursos inclusos
    permite_pagamento_online = models.BooleanField(default=False)
    permite_cupons_desconto = models.BooleanField(default=False)
    permite_whatsapp_bot = models.BooleanField(default=False)
    permite_impressao_termica = models.BooleanField(default=True)
    permite_relatorios_avancados = models.BooleanField(default=False)
    permite_api_integracao = models.BooleanField(default=False)
    permite_area_entregador = models.BooleanField(default=False)
    permite_multi_loja = models.BooleanField(default=False)
    
    # Configurações
    ativo = models.BooleanField(default=True)
    ordem_exibicao = models.PositiveIntegerField(default=0, help_text='Ordem para exibição nos preços')
    destaque = models.BooleanField(default=False, help_text='Destacar como plano recomendado')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['ordem_exibicao', 'preco_mensal']
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
    
    def __str__(self):
        return f"{self.get_nome_display()} - R$ {self.preco_mensal}/mês"
    
    @property
    def recursos_lista(self):
        """Retorna lista de recursos inclusos no plano"""
        recursos = []
        
        if self.nome == 'starter':
            recursos = [
                'Site responsivo',
                'Gestão de produtos',
                'Impressão A4',
                'Dashboard simples',
                f'Até {self.limite_pedidos_mes} pedidos/mês' if self.limite_pedidos_mes else 'Pedidos ilimitados',
                f'Até {self.limite_produtos} produtos' if self.limite_produtos else 'Produtos ilimitados',
            ]
        elif self.nome == 'pro':
            recursos = [
                'Todos os recursos do Starter',
                'Pagamentos online (PIX/Cartão)',
                'Cupons de desconto',
                'WhatsApp Bot integrado',
                'Impressão térmica',
                'Relatórios avançados',
                f'Até {self.limite_pedidos_mes} pedidos/mês' if self.limite_pedidos_mes else 'Pedidos ilimitados',
                f'Até {self.limite_funcionarios} funcionários',
            ]
        elif self.nome == 'multi':
            recursos = [
                'Todos os recursos do Pro',
                'Multi-loja (ilimitado)',
                'API para integração ERP',
                'Área do entregador',
                'Suporte prioritário',
                'Pedidos ilimitados',
                'Produtos ilimitados',
                'Funcionários ilimitados',
            ]
        
        return recursos


class Restaurante(models.Model):
    # Configurações de frete
    frete_fixo = models.BooleanField(default=False, help_text='Usar valor fixo para o frete?')
    valor_frete_fixo = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    valor_frete_padrao = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    valor_adicional_km = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    raio_limite_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Raio máximo de entrega em km')
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
    
    # Plano de assinatura
    plano = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True, 
                             help_text='Plano de assinatura do restaurante')
    data_inicio_plano = models.DateField(null=True, blank=True, 
                                        help_text='Data de início da assinatura')
    data_vencimento_plano = models.DateField(null=True, blank=True, 
                                            help_text='Data de vencimento da mensalidade')
    plano_ativo = models.BooleanField(default=True, 
                                     help_text='Se false, restaurante fica suspenso')
    
    nome = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    descricao = models.TextField()
    logo = models.ImageField(upload_to='restaurantes/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='restaurantes/banners/', null=True, blank=True)
    favicon = models.ImageField(upload_to='restaurantes/favicons/', null=True, blank=True)
    slogan = models.CharField(max_length=200, blank=True)
    mensagem_boas_vindas = models.TextField(blank=True, help_text="Mensagem de boas-vindas exibida na página inicial")
    
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
    
    # Métodos relacionados ao plano de assinatura
    def pode_criar_produto(self):
        """Verifica se pode criar mais produtos baseado no limite do plano"""
        if not self.plano or not self.plano.limite_produtos:
            return True
        
        produtos_atuais = self.produtos.count()
        return produtos_atuais < self.plano.limite_produtos
    
    def pode_criar_funcionario(self):
        """Verifica se pode adicionar mais funcionários baseado no limite do plano"""
        if not self.plano:
            return True
        
        funcionarios_atuais = self.funcionarios.count()
        return funcionarios_atuais < self.plano.limite_funcionarios
    
    def pode_processar_pedido(self):
        """Verifica se pode processar mais pedidos baseado no limite mensal do plano"""
        if not self.plano or not self.plano.limite_pedidos_mes:
            return True
        
        from django.utils import timezone
        hoje = timezone.now().date()
        inicio_mes = hoje.replace(day=1)
        
        pedidos_mes = self.pedidos.filter(
            created_at__date__gte=inicio_mes,
            created_at__date__lte=hoje
        ).exclude(status='cancelado').count()
        
        return pedidos_mes < self.plano.limite_pedidos_mes
    
    def tem_recurso(self, recurso):
        """Verifica se o plano atual permite determinado recurso"""
        if not self.plano:
            return False
        
        recursos_map = {
            'pagamento_online': self.plano.permite_pagamento_online,
            'cupons_desconto': self.plano.permite_cupons_desconto,
            'whatsapp_bot': self.plano.permite_whatsapp_bot,
            'impressao_termica': self.plano.permite_impressao_termica,
            'relatorios_avancados': self.plano.permite_relatorios_avancados,
            'api_integracao': self.plano.permite_api_integracao,
            'area_entregador': self.plano.permite_area_entregador,
            'multi_loja': self.plano.permite_multi_loja,
        }
        
        return recursos_map.get(recurso, False)
    
    def plano_vencido(self):
        """Verifica se o plano está vencido"""
        if not self.data_vencimento_plano:
            return False
        
        from django.utils import timezone
        return timezone.now().date() > self.data_vencimento_plano
    
    def dias_ate_vencimento(self):
        """Retorna quantos dias faltam para o vencimento do plano"""
        if not self.data_vencimento_plano:
            return None
        
        from django.utils import timezone
        hoje = timezone.now().date()
        return (self.data_vencimento_plano - hoje).days


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
    permite_meio_a_meio = models.BooleanField(default=False, help_text="Permite vender este produto como metade de uma pizza")
    tempo_preparo = models.PositiveIntegerField(default=15, help_text="Tempo em minutos")
    
    # Controle de estoque
    estoque_atual = models.PositiveIntegerField(default=0, help_text="Quantidade atual em estoque")
    estoque_minimo = models.PositiveIntegerField(default=5, help_text="Estoque mínimo para alerta")
    controlar_estoque = models.BooleanField(default=False, help_text="Ativar controle de estoque para este produto")
    
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
    
    @property
    def estoque_baixo(self):
        """Verifica se o estoque está baixo"""
        if not self.controlar_estoque:
            return False
        return self.estoque_atual <= self.estoque_minimo
    
    @property
    def estoque_esgotado(self):
        """Verifica se o estoque está esgotado"""
        if not self.controlar_estoque:
            return False
        return self.estoque_atual <= 0


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
    
    # Controle de quantidade para opções checkbox
    quantidade_minima = models.PositiveIntegerField(
        default=0, 
        help_text="Quantidade mínima de itens que devem ser selecionados (apenas para checkbox)"
    )
    quantidade_maxima = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Quantidade máxima de itens que podem ser selecionados (apenas para checkbox). Deixe vazio para ilimitado"
    )
    
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
    def calcular_frete(self):
        """Calcula o valor do frete para o pedido, usando utilitário local e respeitando o raio limite de entrega. Sempre retorna Decimal."""
        from core.utils_frete_cep import calcular_frete_cep
        from decimal import Decimal
        restaurante = self.restaurante
        if restaurante.frete_fixo and restaurante.valor_frete_fixo is not None:
            return Decimal(str(restaurante.valor_frete_fixo))
        if restaurante.valor_frete_padrao is not None:
            valor = Decimal(str(restaurante.valor_frete_padrao))
            if self.endereco_cep and restaurante.cep and restaurante.valor_adicional_km:
                resultado = calcular_frete_cep(
                    cep_destino=self.endereco_cep,
                    cep_referencia=restaurante.cep,
                    taxa_base=float(restaurante.valor_frete_padrao),
                    taxa_km=float(restaurante.valor_adicional_km),
                    raio_limite_km=float(restaurante.raio_limite_km) if restaurante.raio_limite_km else None
                )
                if resultado and 'erro' in resultado:
                    raise Exception(resultado['erro'])
                if resultado and 'custo_frete' in resultado:
                    return Decimal(str(resultado['custo_frete']))
            return valor
        return Decimal('0.0')
    """Modelo para pedidos"""
    STATUS_CHOICES = [
        ('carrinho', 'No Carrinho'),
        ('pendente', 'Pendente de Pagamento'),
        ('confirmado', 'Confirmado'),
        ('preparando', 'Preparando'),
        ('pronto', 'Pronto'),
        ('aguardando_entregador', 'Aguardando Entregador'),
        ('em_entrega', 'Em Entrega'),
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
    entregador = models.ForeignKey('Entregador', null=True, blank=True, on_delete=models.SET_NULL, related_name='pedidos_entrega')
    
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
    valor_entrega = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Valor pago ao entregador")
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status e controle
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='carrinho')
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
    status_anterior = models.CharField(max_length=30, choices=Pedido.STATUS_CHOICES, blank=True, null=True)
    status_novo = models.CharField(max_length=30, choices=Pedido.STATUS_CHOICES)
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


class Notificacao(models.Model):
    """Sistema de notificações para o painel do lojista"""
    TIPO_CHOICES = [
        ('pedido_novo', 'Novo Pedido'),
        ('estoque_baixo', 'Estoque Baixo'),
        ('estoque_esgotado', 'Estoque Esgotado'),
        ('sistema', 'Mensagem do Sistema'),
        ('avaliacao', 'Nova Avaliação'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='notificacoes')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    lida = models.BooleanField(default=False)
    link_acao = models.CharField(max_length=500, blank=True, help_text="Link para ação relacionada (opcional)")
    
    # Referências opcionais
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, null=True, blank=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notificacoes'
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.restaurante.nome} - {self.titulo}"
    
    @property
    def icone(self):
        """Retorna o ícone FontAwesome baseado no tipo"""
        icones = {
            'pedido_novo': 'fas fa-shopping-cart',
            'estoque_baixo': 'fas fa-exclamation-triangle',
            'estoque_esgotado': 'fas fa-times-circle',
            'sistema': 'fas fa-info-circle',
            'avaliacao': 'fas fa-star',
        }
        return icones.get(self.tipo, 'fas fa-bell')
    
    @property
    def cor(self):
        """Retorna a cor baseada na prioridade"""
        cores = {
            'baixa': 'info',
            'media': 'warning',
            'alta': 'danger',
            'urgente': 'danger',
        }
        return cores.get(self.prioridade, 'info')


# ====================== MODELOS DE ENTREGA/MOTOBOYS ======================

class Entregador(models.Model):
    """Modelo para entregadores/motoboys"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    cnh = models.CharField(max_length=20, blank=True, help_text="Número da CNH")
    veiculo = models.CharField(max_length=50, blank=True, help_text="Ex: Moto Honda CG 160")
    dados_bancarios = models.CharField(max_length=100, blank=True, help_text="Dados para pagamento")
    disponivel = models.BooleanField(default=True, help_text="Disponível para receber pedidos")
    em_pausa = models.BooleanField(default=False, help_text="Em pausa temporária")
    nota_media = models.FloatField(default=0, help_text="Média das avaliações")
    total_avaliacoes = models.PositiveIntegerField(default=0)
    total_entregas = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entregadores'
        verbose_name = 'Entregador'
        verbose_name_plural = 'Entregadores'

    def __str__(self):
        return self.nome

    @property
    def status_display(self):
        """Status formatado para exibição"""
        if self.em_pausa:
            return "Em pausa"
        elif self.disponivel:
            return "Disponível"
        else:
            return "Indisponível"

    def atualizar_nota_media(self):
        """Atualiza a nota média baseada nas avaliações"""
        avaliacoes = self.avaliacoes.all()
        if avaliacoes.exists():
            total_notas = sum(av.nota for av in avaliacoes)
            self.nota_media = total_notas / avaliacoes.count()
            self.total_avaliacoes = avaliacoes.count()
            self.save()


class AceitePedido(models.Model):
    """Registro de aceite de pedidos pelos entregadores"""
    STATUS_CHOICES = [
        ('aceito', 'Aceito'),
        ('recusado', 'Recusado'),
        ('expirado', 'Expirado'),
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='aceites')
    entregador = models.ForeignKey(Entregador, on_delete=models.CASCADE, related_name='aceites')
    data_aceite = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aceito')
    observacoes = models.TextField(blank=True)

    class Meta:
        db_table = 'aceite_pedidos'
        verbose_name = 'Aceite de Pedido'
        verbose_name_plural = 'Aceites de Pedidos'
        unique_together = ['pedido', 'entregador']

    def __str__(self):
        return f"{self.entregador.nome} - Pedido #{self.pedido.numero} - {self.get_status_display()}"


class AvaliacaoEntregador(models.Model):
    """Avaliações dos entregadores pelos clientes"""
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='avaliacao_entregador')
    entregador = models.ForeignKey(Entregador, on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comentario = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'avaliacoes_entregador'
        verbose_name = 'Avaliação do Entregador'
        verbose_name_plural = 'Avaliações dos Entregadores'

    def __str__(self):
        return f"Avaliação {self.nota}/5 - {self.entregador.nome} - Pedido #{self.pedido.numero}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza a nota média do entregador
        self.entregador.atualizar_nota_media()


class OcorrenciaEntrega(models.Model):
    """Registro de ocorrências durante a entrega"""
    TIPO_CHOICES = [
        ('cliente_ausente', 'Cliente ausente'),
        ('endereco_errado', 'Endereço incorreto'),
        ('pagamento_recusado', 'Pagamento recusado'),
        ('produto_danificado', 'Produto danificado'),
        ('atraso_restaurante', 'Atraso do restaurante'),
        ('transito_intenso', 'Trânsito intenso'),
        ('veiculo_quebrado', 'Problema com veículo'),
        ('outro', 'Outro'),
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='ocorrencias')
    entregador = models.ForeignKey(Entregador, on_delete=models.CASCADE, related_name='ocorrencias')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descricao = models.TextField(help_text="Descreva detalhadamente a ocorrência")
    data = models.DateTimeField(auto_now_add=True)
    resolvido = models.BooleanField(default=False)
    observacoes_resolucao = models.TextField(blank=True)

    class Meta:
        db_table = 'ocorrencias_entrega'
        verbose_name = 'Ocorrência de Entrega'
        verbose_name_plural = 'Ocorrências de Entrega'
        ordering = ['-data']

    def __str__(self):
        return f"Ocorrência: {self.get_tipo_display()} - Pedido #{self.pedido.numero}"
