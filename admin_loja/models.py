from django.db import models
from core.models import Restaurante
import uuid

class Impressora(models.Model):
    """Modelo para impressoras dos restaurantes"""
    TIPO_CONEXAO_CHOICES = [
        ('usb', 'USB'),
        ('rede', 'Rede/Ethernet'),
        ('wifi', 'Wi-Fi'),
    ]
    
    TIPO_PEDIDO_CHOICES = [
        ('balcao', 'Balcão'),
        ('delivery', 'Delivery'), 
        ('cozinha', 'Cozinha'),
        ('geral', 'Geral'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='impressoras')
    nome = models.CharField(max_length=100, help_text="Nome da impressora (ex: Impressora Cozinha)")
    tipo_conexao = models.CharField(max_length=10, choices=TIPO_CONEXAO_CHOICES)
    
    # Configurações de rede
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP da impressora (para conexões de rede)")
    porta = models.PositiveIntegerField(default=9100, help_text="Porta da impressora")
    
    # Configurações USB
    caminho_usb = models.CharField(max_length=200, blank=True, help_text="Caminho USB (ex: /dev/usb/lp0)")
    
    # Configurações gerais
    ativa = models.BooleanField(default=True)
    padrao_para_tipo = models.CharField(
        max_length=10, 
        choices=TIPO_PEDIDO_CHOICES,
        blank=True,
        help_text="Tipo de pedido para o qual esta impressora é padrão"
    )
    
    # Configurações de impressão
    largura_papel = models.PositiveIntegerField(default=80, help_text="Largura do papel em mm")
    cortar_papel = models.BooleanField(default=True, help_text="Cortar papel após impressão")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'impressoras'
        verbose_name = 'Impressora'
        verbose_name_plural = 'Impressoras'
        unique_together = ['restaurante', 'padrao_para_tipo']
    
    def __str__(self):
        return f"{self.nome} - {self.restaurante.nome}"
    
    def get_connection_string(self):
        """Retorna string de conexão baseada no tipo"""
        if self.tipo_conexao == 'usb':
            return self.caminho_usb
        elif self.tipo_conexao in ['rede', 'wifi']:
            return f"{self.ip_address}:{self.porta}"
        return None
