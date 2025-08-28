"""
Configuração do Celery para o sistema Menuly.
Este arquivo configura o Celery para funcionar com Django,
permitindo o processamento de tarefas assíncronas como:
- Processamento de pedidos
- Envio de notificações
- Cálculos de frete
- Integração com WhatsApp
"""

import os
from celery import Celery
from django.conf import settings

# Define o módulo de configuração padrão do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menuly.settings')

# Cria a instância do Celery
app = Celery('menuly')

# Usa as configurações do Django, procurando por configurações com prefixo CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configurações do Celery
app.conf.update(
    # Broker (Redis)
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # Configurações de tasks
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    
    # Configurações de workers
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # Configurações de beat (agendamento)
    beat_schedule={
        'limpeza-pedidos-expirados': {
            'task': 'core.tasks.limpar_pedidos_expirados',
            'schedule': 300.0,  # A cada 5 minutos
        },
        'atualizar-status-entregas': {
            'task': 'core.tasks.atualizar_status_entregas',
            'schedule': 60.0,   # A cada 1 minuto
        },
    },
)

# Descobre automaticamente as tasks em todos os apps Django instalados
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Task de debug para testar se o Celery está funcionando"""
    print(f'Request: {self.request!r}')