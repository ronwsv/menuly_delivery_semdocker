"""
Tasks do Celery para o sistema Menuly.
Este arquivo contém as tarefas assíncronas que são executadas pelo Celery.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def limpar_pedidos_expirados(self):
    """
    Remove pedidos que estão pendentes há mais de 30 minutos.
    Esta task é executada a cada 5 minutos pelo Celery Beat.
    """
    try:
        from core.models import Pedido, StatusPedido
        
        # Calcula o tempo limite (30 minutos atrás)
        tempo_limite = timezone.now() - timedelta(minutes=30)
        
        # Busca pedidos pendentes que estão expirados
        pedidos_expirados = Pedido.objects.filter(
            status=StatusPedido.PENDENTE,
            data_criacao__lt=tempo_limite
        )
        
        count = pedidos_expirados.count()
        
        if count > 0:
            # Atualiza o status para cancelado
            pedidos_expirados.update(status=StatusPedido.CANCELADO)
            logger.info(f"Limpeza de pedidos: {count} pedidos expirados foram cancelados")
        
        return f"Processados {count} pedidos expirados"
        
    except Exception as exc:
        logger.error(f"Erro na limpeza de pedidos expirados: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def atualizar_status_entregas(self):
    """
    Atualiza o status das entregas em andamento.
    Esta task é executada a cada 1 minuto pelo Celery Beat.
    """
    try:
        from core.models import Pedido, StatusPedido
        
        # Busca pedidos em entrega há mais de 2 horas
        tempo_limite = timezone.now() - timedelta(hours=2)
        
        pedidos_entrega_longa = Pedido.objects.filter(
            status=StatusPedido.EM_ENTREGA,
            data_atualizacao__lt=tempo_limite
        )
        
        count = 0
        for pedido in pedidos_entrega_longa:
            # Aqui você pode implementar lógica específica
            # Por exemplo, notificar o cliente ou o restaurante
            logger.warning(f"Pedido {pedido.id} está em entrega há mais de 2 horas")
            count += 1
        
        return f"Verificados {count} pedidos com entrega demorada"
        
    except Exception as exc:
        logger.error(f"Erro na atualização de status de entregas: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True)
def processar_pedido(self, pedido_id):
    """
    Processa um pedido específico de forma assíncrona.
    
    Args:
        pedido_id (int): ID do pedido a ser processado
    """
    try:
        from core.models import Pedido, StatusPedido
        from core.notifications import enviar_notificacao_pedido
        
        pedido = Pedido.objects.get(id=pedido_id)
        
        # Confirma o pedido
        pedido.status = StatusPedido.CONFIRMADO
        pedido.save()
        
        # Envia notificações
        enviar_notificacao_pedido(pedido, 'confirmado')
        
        logger.info(f"Pedido {pedido_id} processado com sucesso")
        return f"Pedido {pedido_id} processado"
        
    except Exception as exc:
        logger.error(f"Erro ao processar pedido {pedido_id}: {exc}")
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@shared_task(bind=True)
def enviar_notificacao_whatsapp(self, numero, mensagem):
    """
    Envia uma notificação via WhatsApp de forma assíncrona.
    
    Args:
        numero (str): Número do WhatsApp
        mensagem (str): Mensagem a ser enviada
    """
    try:
        # Aqui você implementaria a integração com WhatsApp
        # Por enquanto, apenas loga a mensagem
        logger.info(f"WhatsApp para {numero}: {mensagem}")
        
        return f"Notificação enviada para {numero}"
        
    except Exception as exc:
        logger.error(f"Erro ao enviar WhatsApp para {numero}: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task
def calcular_frete_async(restaurante_id, cep_destino):
    """
    Calcula o frete de forma assíncrona.
    
    Args:
        restaurante_id (int): ID do restaurante
        cep_destino (str): CEP de destino
        
    Returns:
        dict: Informações do frete calculado
    """
    try:
        from core.utils_frete_cep import calcular_frete
        from core.models import Restaurante
        
        restaurante = Restaurante.objects.get(id=restaurante_id)
        resultado = calcular_frete(restaurante, cep_destino)
        
        return {
            'sucesso': True,
            'valor': resultado.get('valor', 0),
            'tempo_estimado': resultado.get('tempo_estimado', 'Não disponível')
        }
        
    except Exception as exc:
        logger.error(f"Erro no cálculo de frete: {exc}")
        return {
            'sucesso': False,
            'erro': str(exc)
        }


@shared_task
def debug_task():
    """Task de debug para testar se o Celery está funcionando"""
    return 'Celery está funcionando!'