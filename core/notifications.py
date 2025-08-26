"""
Sistema de notificações para entregadores e lojistas
"""

from django.core.mail import send_mail
from django.conf import settings
from .models import Notificacao, Entregador, Pedido
import logging

logger = logging.getLogger(__name__)


def criar_notificacao(restaurante, tipo, titulo, mensagem, prioridade='media', 
                     pedido=None, produto=None, link_acao=None):
    """Cria uma notificação no sistema"""
    try:
        notificacao = Notificacao.objects.create(
            restaurante=restaurante,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            prioridade=prioridade,
            pedido=pedido,
            produto=produto,
            link_acao=link_acao
        )
        logger.info(f"Notificação criada: {titulo} para {restaurante.nome}")
        return notificacao
    except Exception as e:
        logger.error(f"Erro ao criar notificação: {e}")
        return None


def notificar_novo_pedido(pedido):
    """Notifica sobre novo pedido aguardando entregador"""
    try:
        # Notificação para o restaurante
        criar_notificacao(
            restaurante=pedido.restaurante,
            tipo='pedido_novo',
            titulo=f'Novo pedido #{pedido.numero}',
            mensagem=f'Pedido de {pedido.cliente_nome} aguardando entregador. Total: R$ {pedido.total}',
            prioridade='alta',
            pedido=pedido,
            link_acao=f'/admin-loja/pedidos/{pedido.id}/'
        )
        
        # Notificar todos os entregadores disponíveis
        notificar_entregadores_pedido_disponivel(pedido)
        
    except Exception as e:
        logger.error(f"Erro ao notificar novo pedido {pedido.numero}: {e}")


def notificar_entregadores_pedido_disponivel(pedido):
    """Notifica entregadores sobre pedido disponível"""
    try:
        entregadores_disponiveis = Entregador.objects.filter(
            disponivel=True,
            em_pausa=False
        )
        
        for entregador in entregadores_disponiveis:
            # Aqui você pode implementar diferentes tipos de notificação:
            # 1. Push notification (Firebase)
            # 2. SMS
            # 3. Email
            # 4. WebSocket para app em tempo real
            
            # Por enquanto, vamos criar uma notificação de sistema
            if hasattr(entregador.usuario, 'email') and entregador.usuario.email:
                enviar_email_pedido_disponivel(entregador, pedido)
            
            logger.info(f"Notificado entregador {entregador.nome} sobre pedido #{pedido.numero}")
            
    except Exception as e:
        logger.error(f"Erro ao notificar entregadores sobre pedido {pedido.numero}: {e}")


def notificar_pedido_aceito(pedido, entregador):
    """Notifica que pedido foi aceito por um entregador"""
    try:
        # Notificar o restaurante
        criar_notificacao(
            restaurante=pedido.restaurante,
            tipo='pedido_novo',
            titulo=f'Pedido #{pedido.numero} aceito',
            mensagem=f'Entregador {entregador.nome} aceitou o pedido. Tel: {entregador.telefone}',
            prioridade='media',
            pedido=pedido,
            link_acao=f'/admin-loja/pedidos/{pedido.id}/'
        )
        
        # Email para o cliente (opcional)
        if pedido.cliente_email:
            enviar_email_pedido_aceito(pedido, entregador)
            
    except Exception as e:
        logger.error(f"Erro ao notificar aceite do pedido {pedido.numero}: {e}")


def notificar_entregador_atribuido(pedido, entregador):
    """Notifica entregador que foi atribuído manualmente a um pedido"""
    try:
        if hasattr(entregador.usuario, 'email') and entregador.usuario.email:
            enviar_email_entregador_atribuido(entregador, pedido)
        
        logger.info(f"Notificado entregador {entregador.nome} sobre atribuição do pedido #{pedido.numero}")
        
    except Exception as e:
        logger.error(f"Erro ao notificar atribuição para {entregador.nome}: {e}")


def notificar_ocorrencia_entrega(ocorrencia):
    """Notifica sobre nova ocorrência na entrega"""
    try:
        criar_notificacao(
            restaurante=ocorrencia.pedido.restaurante,
            tipo='sistema',
            titulo=f'Ocorrência na entrega #{ocorrencia.pedido.numero}',
            mensagem=f'{ocorrencia.get_tipo_display()}: {ocorrencia.descricao[:100]}...',
            prioridade='alta',
            pedido=ocorrencia.pedido,
            link_acao=f'/admin-loja/ocorrencias/{ocorrencia.id}/'
        )
        
    except Exception as e:
        logger.error(f"Erro ao notificar ocorrência {ocorrencia.id}: {e}")


def enviar_email_pedido_disponivel(entregador, pedido):
    """Envia email para entregador sobre pedido disponível"""
    try:
        assunto = f'[Menuly] Novo pedido disponível - #{pedido.numero}'
        mensagem = f"""
        Olá {entregador.nome},
        
        Um novo pedido está disponível para entrega:
        
        📦 Pedido: #{pedido.numero}
        🏪 Restaurante: {pedido.restaurante.nome}
        📍 Destino: {pedido.endereco_bairro}, {pedido.cidade}
        💰 Valor da entrega: R$ {pedido.valor_entrega}
        📱 Cliente: {pedido.cliente_nome} - {pedido.cliente_celular}
        
        Acesse o app para aceitar o pedido.
        
        Menuly Delivery
        """
        
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [entregador.usuario.email],
            fail_silently=True
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar email para {entregador.nome}: {e}")


def enviar_email_pedido_aceito(pedido, entregador):
    """Envia email para cliente informando que pedido foi aceito"""
    try:
        assunto = f'[{pedido.restaurante.nome}] Seu pedido #{pedido.numero} está a caminho!'
        mensagem = f"""
        Olá {pedido.cliente_nome},
        
        Ótima notícia! Seu pedido foi aceito e está a caminho:
        
        🛍️ Pedido: #{pedido.numero}
        🏍️ Entregador: {entregador.nome}
        📱 Telefone: {entregador.telefone}
        ⭐ Avaliação: {entregador.nota_media:.1f}/5.0 ({entregador.total_avaliacoes} avaliações)
        
        Tempo estimado de entrega: {pedido.tempo_entrega_estimado} minutos
        
        Obrigado por escolher {pedido.restaurante.nome}!
        """
        
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [pedido.cliente_email],
            fail_silently=True
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar email para cliente do pedido {pedido.numero}: {e}")


def enviar_email_entregador_atribuido(entregador, pedido):
    """Envia email informando que entregador foi atribuído a um pedido"""
    try:
        assunto = f'[Menuly] Você foi designado para entrega - #{pedido.numero}'
        mensagem = f"""
        Olá {entregador.nome},
        
        Você foi designado para realizar uma entrega:
        
        📦 Pedido: #{pedido.numero}
        🏪 Restaurante: {pedido.restaurante.nome}
        📍 Endereço: {pedido.endereco_logradouro}, {pedido.endereco_numero}
        📍 Bairro: {pedido.endereco_bairro}, {pedido.endereco_cidade}
        💰 Valor da entrega: R$ {pedido.valor_entrega}
        📱 Cliente: {pedido.cliente_nome} - {pedido.cliente_celular}
        
        Por favor, dirija-se ao restaurante para retirar o pedido.
        
        Menuly Delivery
        """
        
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [entregador.usuario.email],
            fail_silently=True
        )
        
    except Exception as e:
        logger.error(f"Erro ao enviar email de atribuição para {entregador.nome}: {e}")


# Classe para integração com serviços de push notification
class PushNotificationService:
    """Classe para enviar push notifications"""
    
    @staticmethod
    def enviar_para_entregadores(titulo, corpo, dados_extras=None):
        """Envia push notification para todos os entregadores"""
        # TODO: Integrar com Firebase Cloud Messaging
        # ou outro serviço de push notification
        pass
    
    @staticmethod
    def enviar_para_entregador(entregador, titulo, corpo, dados_extras=None):
        """Envia push notification para um entregador específico"""
        # TODO: Implementar envio individual
        pass
    
    @staticmethod
    def enviar_para_cliente(cliente, titulo, corpo, dados_extras=None):
        """Envia push notification para cliente"""
        # TODO: Implementar notificação para cliente
        pass


# Funções utilitárias para timeout de pedidos
def verificar_pedidos_sem_entregador():
    """Verifica pedidos aguardando entregador há muito tempo"""
    from django.utils import timezone
    from datetime import timedelta
    
    tempo_limite = timezone.now() - timedelta(minutes=15)  # 15 minutos
    
    pedidos_abandonados = Pedido.objects.filter(
        status='aguardando_entregador',
        updated_at__lt=tempo_limite
    )
    
    for pedido in pedidos_abandonados:
        criar_notificacao(
            restaurante=pedido.restaurante,
            tipo='sistema',
            titulo=f'Pedido #{pedido.numero} sem entregador',
            mensagem=f'Pedido aguarda entregador há mais de 15 minutos. Considere atribuir manualmente.',
            prioridade='urgente',
            pedido=pedido,
            link_acao=f'/admin-loja/pedidos/{pedido.id}/'
        )
    
    return pedidos_abandonados.count()


# Task para ser executada com Celery (opcional)
def task_verificar_pedidos_timeout():
    """Task para verificar pedidos em timeout (usar com Celery)"""
    try:
        count = verificar_pedidos_sem_entregador()
        logger.info(f"Verificação de timeout executada. {count} pedidos em alerta.")
        return count
    except Exception as e:
        logger.error(f"Erro na verificação de timeout: {e}")
        return 0