"""
Sistema Híbrido de Carrinho - Migração Gradual
Permite coexistência entre carrinho de sessões e carrinho persistente
"""

from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

from .models import Carrinho, CarrinhoItem, Produto, Restaurante
from .services import CarrinhoService

logger = logging.getLogger(__name__)


class CarrinhoHybridService:
    """
    Serviço híbrido que gerencia a transição gradual do carrinho de sessões 
    para o carrinho persistente sem impacto no usuário
    """
    
    @staticmethod
    def obter_carrinho_ativo(request, restaurante):
        """
        Obtém o carrinho ativo priorizando o novo sistema,
        mas mantendo compatibilidade com sessões
        """
        usuario = request.user if request.user.is_authenticated else None
        sessao_id = request.session.session_key
        
        # 1. Tentar obter carrinho persistente (novo sistema)
        try:
            carrinho_persistente = CarrinhoService.obter_carrinho(
                usuario=usuario,
                sessao_id=sessao_id,
                restaurante=restaurante
            )
            
            # Se tem itens no carrinho persistente, usar ele
            if not carrinho_persistente.esta_vazio():
                return {
                    'carrinho': carrinho_persistente,
                    'tipo': 'persistente',
                    'precisa_migracao': False
                }
        except Exception as e:
            logger.warning(f"Erro ao acessar carrinho persistente: {e}")
        
        # 2. Verificar se tem carrinho na sessão (sistema antigo)
        carrinho_sessao = request.session.get('carrinho', {})
        
        if carrinho_sessao:
            # Tem carrinho na sessão - precisa migrar
            try:
                # Migrar automaticamente
                carrinho_persistente = CarrinhoHybridService._migrar_carrinho_sessao(
                    carrinho_sessao, usuario, sessao_id, restaurante, request
                )
                
                return {
                    'carrinho': carrinho_persistente,
                    'tipo': 'migrado',
                    'precisa_migracao': False
                }
            except Exception as e:
                logger.error(f"Erro na migração automática: {e}")
                # Se falhou, continua usando sessão temporariamente
                return {
                    'carrinho_sessao': carrinho_sessao,
                    'tipo': 'sessao',
                    'precisa_migracao': True
                }
        
        # 3. Carrinho vazio - criar novo persistente
        carrinho_persistente = CarrinhoService.obter_carrinho(
            usuario=usuario,
            sessao_id=sessao_id,
            restaurante=restaurante
        )
        
        return {
            'carrinho': carrinho_persistente,
            'tipo': 'novo_persistente',
            'precisa_migracao': False
        }
    
    @staticmethod
    def _migrar_carrinho_sessao(carrinho_sessao, usuario, sessao_id, restaurante, request):
        """
        Migra carrinho de sessão para carrinho persistente
        """
        logger.info(f"Iniciando migração de carrinho - Usuário: {usuario}, Sessão: {sessao_id}")
        
        # Obter carrinho persistente
        carrinho_persistente = CarrinhoService.obter_carrinho(
            usuario=usuario,
            sessao_id=sessao_id,
            restaurante=restaurante
        )
        
        # Migrar cada item
        itens_migrados = 0
        for item_key, item_data in carrinho_sessao.items():
            try:
                # Extrair ID do produto
                produto_id = item_data.get('produto_id')
                if '_' in item_key and not produto_id:
                    produto_id = item_key.split('_')[0]
                
                if not produto_id:
                    continue
                
                produto = Produto.objects.get(id=produto_id)
                
                # Preparar dados de personalização
                personalizacoes = item_data.get('personalizacoes', [])
                meio_a_meio = item_data.get('meio_a_meio')
                
                # Adicionar ao carrinho persistente
                CarrinhoService.adicionar_item(
                    carrinho=carrinho_persistente,
                    produto=produto,
                    quantidade=item_data.get('quantidade', 1),
                    observacoes=item_data.get('observacoes', ''),
                    personalizacoes=personalizacoes,
                    dados_meio_a_meio=meio_a_meio
                )
                
                itens_migrados += 1
                
            except Exception as e:
                logger.error(f"Erro ao migrar item {item_key}: {e}")
                continue
        
        # Limpar carrinho da sessão após migração bem-sucedida
        if itens_migrados > 0:
            request.session['carrinho'] = {}
            request.session.modified = True
            logger.info(f"Migração concluída: {itens_migrados} itens migrados")
        
        return carrinho_persistente
    
    @staticmethod
    def adicionar_item_hybrid(request, restaurante, produto, quantidade=1, **kwargs):
        """
        Adiciona item usando sistema híbrido
        """
        # Obter carrinho ativo
        carrinho_info = CarrinhoHybridService.obter_carrinho_ativo(request, restaurante)
        
        if carrinho_info['tipo'] == 'sessao':
            # Usar sistema antigo temporariamente
            return CarrinhoHybridService._adicionar_item_sessao(
                request, produto, quantidade, **kwargs
            )
        else:
            # Usar sistema novo
            return CarrinhoService.adicionar_item(
                carrinho=carrinho_info['carrinho'],
                produto=produto,
                quantidade=quantidade,
                **kwargs
            )
    
    @staticmethod
    def _adicionar_item_sessao(request, produto, quantidade, observacoes="", 
                              personalizacoes=None, dados_meio_a_meio=None):
        """
        Fallback para adicionar item no sistema de sessões
        """
        carrinho = request.session.get('carrinho', {})
        
        # Gerar chave do item
        item_key = str(produto.id)
        if personalizacoes or dados_meio_a_meio:
            import hashlib
            dados_hash = str(personalizacoes) + str(dados_meio_a_meio)
            hash_suffix = hashlib.md5(dados_hash.encode()).hexdigest()[:8]
            item_key = f"{produto.id}_{hash_suffix}"
        
        # Adicionar/atualizar item
        if item_key in carrinho:
            carrinho[item_key]['quantidade'] += quantidade
        else:
            carrinho[item_key] = {
                'produto_id': str(produto.id),
                'nome': produto.nome,
                'preco': float(produto.preco_final),
                'quantidade': quantidade,
                'observacoes': observacoes,
                'personalizacoes': personalizacoes or [],
                'meio_a_meio': dados_meio_a_meio,
            }
        
        request.session['carrinho'] = carrinho
        request.session.modified = True
        
        return carrinho[item_key]
    
    @staticmethod
    def calcular_resumo_hybrid(request, restaurante):
        """
        Calcula resumo do carrinho usando sistema híbrido
        """
        carrinho_info = CarrinhoHybridService.obter_carrinho_ativo(request, restaurante)
        
        if carrinho_info['tipo'] == 'sessao':
            return CarrinhoHybridService._calcular_resumo_sessao(carrinho_info['carrinho_sessao'])
        else:
            return CarrinhoService.calcular_resumo(carrinho_info['carrinho'])
    
    @staticmethod
    def _calcular_resumo_sessao(carrinho_sessao):
        """
        Fallback para calcular resumo do carrinho de sessão
        """
        total_itens = 0
        subtotal = Decimal('0.00')
        itens_detalhados = []
        
        for item_key, item in carrinho_sessao.items():
            item_subtotal = Decimal(str(item['preco'])) * item['quantidade']
            subtotal += item_subtotal
            total_itens += item['quantidade']
            
            itens_detalhados.append({
                'id': item_key,
                'produto': {
                    'id': item['produto_id'],
                    'nome': item['nome'],
                },
                'quantidade': item['quantidade'],
                'preco_unitario': Decimal(str(item['preco'])),
                'subtotal': item_subtotal,
                'observacoes': item.get('observacoes', ''),
                'eh_meio_a_meio': bool(item.get('meio_a_meio')),
                'personalizacoes': item.get('personalizacoes', []),
            })
        
        return {
            'itens': itens_detalhados,
            'total_itens': total_itens,
            'subtotal': subtotal,
            'carrinho_vazio': len(carrinho_sessao) == 0,
        }