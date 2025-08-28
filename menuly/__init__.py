# Importa a aplicação Celery para garantir que seja carregada quando o Django iniciar
from .celery import app as celery_app

__all__ = ('celery_app',)