"""
Tasks otimizadas do Celery para o sistema Menuly.
Versão corrigida sem dependências de classes inexistentes.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def limpar_pedidos_expirados(self):
    """Remove pedidos pendentes há mais de 30 minutos."""
    try:
        from core.models import Pedido
        
        tempo_limite = timezone.now() - timedelta(minutes=30)
        pedidos_expirados = Pedido.objects.filter(
            status='pendente',
            data_criacao__lt=tempo_limite
        )
        
        count = pedidos_expirados.count()
        if count > 0:
            pedidos_expirados.update(status='cancelado')
            logger.info(f"✅ {count} pedidos expirados cancelados")
        
        return f"Processados {count} pedidos expirados"
        
    except Exception as exc:
        logger.error(f"❌ Erro na limpeza de pedidos: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(bind=True) 
def verificar_entregas_demoradas(self):
    """Verifica entregas que estão demorando muito."""
    try:
        from core.models import Pedido
        
        tempo_limite = timezone.now() - timedelta(hours=2)
        pedidos_demorados = Pedido.objects.filter(
            status='em_entrega',
            data_atualizacao__lt=tempo_limite
        )
        
        count = pedidos_demorados.count()
        for pedido in pedidos_demorados:
            logger.warning(f"⚠️ Pedido {pedido.id} em entrega há mais de 2h")
        
        return f"Verificados {count} pedidos com entrega demorada"
        
    except Exception as exc:
        logger.error(f"❌ Erro na verificação de entregas: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task
def debug_celery():
    """Task simples para testar se o Celery funciona."""
    return "🚀 Celery funcionando perfeitamente!"