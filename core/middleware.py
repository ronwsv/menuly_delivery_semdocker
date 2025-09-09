"""
Middleware para migração gradual do carrinho
Facilita a transição automática sem impacto no usuário
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class CarrinhoMigrationMiddleware(MiddlewareMixin):
    """
    Middleware que facilita a migração automática do carrinho
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configurações do middleware
        self.migration_enabled = getattr(settings, 'CARRINHO_MIGRATION_ENABLED', True)
        self.log_migration = getattr(settings, 'CARRINHO_MIGRATION_LOG', True)
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Processa request para detectar necessidade de migração
        """
        if not self.migration_enabled:
            return None
        
        # Adicionar flag para indicar se é primeira visita após implementação
        if not hasattr(request, '_carrinho_checked'):
            request._carrinho_checked = True
            
            # Verificar se tem carrinho na sessão que precisa migração
            carrinho_sessao = request.session.get('carrinho', {})
            if carrinho_sessao:
                request._has_legacy_cart = True
                if self.log_migration:
                    logger.info(f"Carrinho legacy detectado - Sessão: {request.session.session_key}")
            else:
                request._has_legacy_cart = False
        
        return None
    
    def process_response(self, request, response):
        """
        Processa response para logs e métricas
        """
        if not self.migration_enabled:
            return response
        
        # Log de migração bem-sucedida
        if hasattr(request, '_migration_success') and request._migration_success:
            if self.log_migration:
                logger.info(f"Migração de carrinho bem-sucedida - Sessão: {request.session.session_key}")
        
        # Adicionar headers para debug (apenas em desenvolvimento)
        if settings.DEBUG and hasattr(request, '_has_legacy_cart'):
            response['X-Carrinho-Legacy'] = str(request._has_legacy_cart)
            if hasattr(request, '_carrinho_type'):
                response['X-Carrinho-Type'] = request._carrinho_type
        
        return response


class CarrinhoDebugMiddleware(MiddlewareMixin):
    """
    Middleware para debug da migração (apenas desenvolvimento)
    """
    
    def process_request(self, request):
        if not settings.DEBUG:
            return None
        
        # Adicionar informações de debug no contexto
        carrinho_sessao = request.session.get('carrinho', {})
        request._debug_carrinho = {
            'has_session_cart': bool(carrinho_sessao),
            'session_items': len(carrinho_sessao),
            'session_key': request.session.session_key,
            'user_authenticated': request.user.is_authenticated,
        }
        
        return None