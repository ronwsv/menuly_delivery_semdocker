"""
Services para lógica de negócio do sistema Menuly.
Implementa o padrão Service Layer para separar a lógica de negócio das views.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.sessions.models import Session
from decimal import Decimal
from typing import Optional, List, Dict, Any
import logging

from .models import (
    Carrinho, CarrinhoItem, CarrinhoItemPersonalizacao,
    Produto, Usuario, Restaurante, Pedido, ItemPedido, 
    PersonalizacaoItemPedido, HistoricoStatusPedido,
    ItemPersonalizacao
)

logger = logging.getLogger(__name__)


class CarrinhoService:
    """Serviço para gestão do carrinho de compras"""
    
    @staticmethod
    def obter_carrinho(usuario: Optional[Usuario] = None, 
                      sessao_id: Optional[str] = None, 
                      restaurante: Optional[Restaurante] = None) -> Carrinho:
        """
        Obtém ou cria um carrinho para o usuário/sessão no restaurante
        """
        if not restaurante:
            raise ValidationError("Restaurante é obrigatório")
        
        if usuario:
            carrinho, created = Carrinho.objects.get_or_create(
                usuario=usuario,
                restaurante=restaurante,
                defaults={'sessao_id': None}
            )
        elif sessao_id:
            carrinho, created = Carrinho.objects.get_or_create(
                sessao_id=sessao_id,
                restaurante=restaurante,
                usuario=None,
                defaults={}
            )
        else:
            raise ValidationError("É necessário informar usuário ou sessão")
        
        # Log para debug
        if created:
            logger.info(f"Novo carrinho criado: {carrinho}")
        
        return carrinho
    
    @staticmethod
    @transaction.atomic
    def adicionar_item(carrinho: Carrinho, 
                      produto: Produto, 
                      quantidade: int = 1,
                      observacoes: str = "",
                      personalizacoes: List[Dict] = None,
                      dados_meio_a_meio: Dict = None) -> CarrinhoItem:
        """
        Adiciona um item ao carrinho com validações
        """
        # Validações básicas
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        
        if not produto.disponivel:
            raise ValidationError(f"Produto '{produto.nome}' não está disponível")
        
        if produto.estoque_esgotado:
            raise ValidationError(f"Produto '{produto.nome}' está em falta")
        
        # Verificar se tem estoque suficiente
        if produto.controlar_estoque and produto.estoque_atual < quantidade:
            raise ValidationError(f"Estoque insuficiente para '{produto.nome}'. Disponível: {produto.estoque_atual}")
        
        # Preparar dados de personalização
        dados_personalizacao = {}
        if personalizacoes:
            dados_personalizacao['personalizacoes'] = personalizacoes
        if dados_meio_a_meio:
            dados_personalizacao['meio_a_meio'] = dados_meio_a_meio
        
        # Verificar se já existe item idêntico no carrinho
        try:
            item_existente = CarrinhoItem.objects.get(
                carrinho=carrinho,
                produto=produto,
                dados_personalizacao=dados_personalizacao
            )
            # Se existe, apenas incrementa a quantidade
            item_existente.quantidade += quantidade
            item_existente.save()
            logger.info(f"Quantidade incrementada no item existente: {item_existente}")
            return item_existente
        
        except CarrinhoItem.DoesNotExist:
            # Se não existe, cria novo item
            item = CarrinhoItem.objects.create(
                carrinho=carrinho,
                produto=produto,
                quantidade=quantidade,
                preco_unitario=produto.preco_final,
                observacoes=observacoes,
                dados_personalizacao=dados_personalizacao
            )
            
            # Criar personalizações relacionadas se existirem
            if personalizacoes:
                for perso_data in personalizacoes:
                    try:
                        item_personalizacao = ItemPersonalizacao.objects.get(
                            id=perso_data.get('item_id')
                        )
                        CarrinhoItemPersonalizacao.objects.create(
                            carrinho_item=item,
                            item_personalizacao=item_personalizacao
                        )
                    except ItemPersonalizacao.DoesNotExist:
                        logger.warning(f"ItemPersonalizacao não encontrado: {perso_data.get('item_id')}")
                        continue
            
            logger.info(f"Novo item adicionado ao carrinho: {item}")
            return item
    
    @staticmethod
    @transaction.atomic
    def remover_item(carrinho: Carrinho, item_id: str) -> bool:
        """
        Remove um item específico do carrinho
        """
        try:
            item = CarrinhoItem.objects.get(id=item_id, carrinho=carrinho)
            item.delete()
            logger.info(f"Item removido do carrinho: {item}")
            return True
        except CarrinhoItem.DoesNotExist:
            logger.warning(f"Tentativa de remover item inexistente: {item_id}")
            return False
    
    @staticmethod
    @transaction.atomic
    def alterar_quantidade(carrinho: Carrinho, item_id: str, nova_quantidade: int) -> bool:
        """
        Altera a quantidade de um item no carrinho
        """
        if nova_quantidade <= 0:
            return CarrinhoService.remover_item(carrinho, item_id)
        
        try:
            item = CarrinhoItem.objects.get(id=item_id, carrinho=carrinho)
            
            # Verificar estoque se aplicável
            if item.produto.controlar_estoque and item.produto.estoque_atual < nova_quantidade:
                raise ValidationError(f"Estoque insuficiente para '{item.produto.nome}'. Disponível: {item.produto.estoque_atual}")
            
            item.quantidade = nova_quantidade
            item.save()
            logger.info(f"Quantidade alterada no item: {item} para {nova_quantidade}")
            return True
            
        except CarrinhoItem.DoesNotExist:
            logger.warning(f"Tentativa de alterar quantidade de item inexistente: {item_id}")
            return False
    
    @staticmethod
    def calcular_resumo(carrinho: Carrinho) -> Dict[str, Any]:
        """
        Calcula o resumo completo do carrinho
        """
        itens = carrinho.itens.select_related('produto').all()
        
        subtotal = Decimal('0.00')
        total_itens = 0
        
        itens_detalhados = []
        
        for item in itens:
            item_subtotal = item.subtotal
            subtotal += item_subtotal
            total_itens += item.quantidade
            
            # Para meio-a-meio, usar nome customizado se disponível
            dados_meio_a_meio = item.dados_personalizacao.get('meio_a_meio', {})
            nome_produto = dados_meio_a_meio.get('nome_customizado')
            if not nome_produto and item.produto:
                nome_produto = item.produto.nome
            elif not nome_produto:
                nome_produto = "Produto Indisponível"
            
            itens_detalhados.append({
                'id': str(item.id),
                'produto': {
                    'id': str(item.produto.id),
                    'nome': nome_produto,
                    'categoria': item.produto.categoria.nome if item.produto.categoria else '',
                    'imagem': item.produto.imagem_principal.url if item.produto.imagem_principal else None,
                },
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'subtotal': item_subtotal,
                'observacoes': item.observacoes,
                'eh_meio_a_meio': item.eh_meio_a_meio,
                'personalizacoes': item.dados_personalizacao.get('personalizacoes', []),
                'meio_a_meio_data': dados_meio_a_meio if dados_meio_a_meio else None,
            })
        
        return {
            'itens': itens_detalhados,
            'total_itens': total_itens,
            'subtotal': subtotal,
            'carrinho_vazio': carrinho.esta_vazio(),
        }
    
    @staticmethod
    @transaction.atomic
    def limpar_carrinho(carrinho: Carrinho) -> bool:
        """
        Remove todos os itens do carrinho
        """
        try:
            carrinho.limpar()
            logger.info(f"Carrinho limpo: {carrinho}")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar carrinho {carrinho}: {e}")
            return False
    
    @staticmethod
    def migrar_carrinho_sessao_para_usuario(sessao_id: str, usuario: Usuario, restaurante: Restaurante):
        """
        Migra itens do carrinho de sessão para usuário logado
        """
        try:
            with transaction.atomic():
                # Buscar carrinho da sessão
                carrinho_sessao = Carrinho.objects.filter(
                    sessao_id=sessao_id,
                    restaurante=restaurante,
                    usuario=None
                ).first()
                
                if not carrinho_sessao or carrinho_sessao.esta_vazio():
                    return
                
                # Obter ou criar carrinho do usuário
                carrinho_usuario = CarrinhoService.obter_carrinho(
                    usuario=usuario, 
                    restaurante=restaurante
                )
                
                # Migrar itens
                for item in carrinho_sessao.itens.all():
                    CarrinhoService.adicionar_item(
                        carrinho=carrinho_usuario,
                        produto=item.produto,
                        quantidade=item.quantidade,
                        observacoes=item.observacoes,
                        personalizacoes=item.dados_personalizacao.get('personalizacoes', []),
                        dados_meio_a_meio=item.dados_personalizacao.get('meio_a_meio')
                    )
                
                # Remover carrinho da sessão
                carrinho_sessao.delete()
                logger.info(f"Carrinho migrado da sessão {sessao_id} para usuário {usuario}")
                
        except Exception as e:
            logger.error(f"Erro ao migrar carrinho: {e}")
            raise


class PedidoService:
    """Serviço para gestão de pedidos"""
    
    @staticmethod
    @transaction.atomic
    def criar_pedido_do_carrinho(carrinho: Carrinho, 
                                dados_cliente: Dict[str, Any],
                                dados_entrega: Dict[str, Any],
                                forma_pagamento: str,
                                observacoes: str = "",
                                troco_para: Optional[Decimal] = None) -> Pedido:
        """
        Cria um pedido a partir do carrinho com todas as validações
        """
        from .services import FreteService  # Import local para evitar circular
        
        # Validações básicas
        if carrinho.esta_vazio():
            raise ValidationError("Carrinho está vazio")
        
        # Validar dados do cliente
        if not dados_cliente.get('nome'):
            raise ValidationError("Nome do cliente é obrigatório")
        if not dados_cliente.get('celular'):
            raise ValidationError("Celular do cliente é obrigatório")
        
        # Obter ou criar usuário
        usuario = PedidoService._obter_ou_criar_usuario(dados_cliente)
        
        # Criar pedido
        pedido = Pedido.objects.create(
            restaurante=carrinho.restaurante,
            cliente=usuario,
            cliente_nome=dados_cliente['nome'],
            cliente_celular=dados_cliente['celular'],
            cliente_email=dados_cliente.get('email', ''),
            tipo_entrega=dados_entrega.get('tipo', 'delivery'),
            forma_pagamento=forma_pagamento,
            observacoes=observacoes,
            troco_para=troco_para,
            status='pendente'
        )
        
        # Adicionar dados de endereço se delivery
        if pedido.tipo_entrega == 'delivery':
            PedidoService._adicionar_endereco_entrega(pedido, dados_entrega)
        
        # Criar itens do pedido
        subtotal_pedido = Decimal('0.00')
        for carrinho_item in carrinho.itens.all():
            item_pedido = ItemPedido.objects.create(
                pedido=pedido,
                produto=carrinho_item.produto,
                produto_nome=carrinho_item.produto.nome,
                produto_preco=carrinho_item.produto.preco_final,
                quantidade=carrinho_item.quantidade,
                preco_unitario=carrinho_item.preco_unitario,
                subtotal=carrinho_item.subtotal,
                observacoes=carrinho_item.observacoes,
                meio_a_meio=carrinho_item.dados_personalizacao.get('meio_a_meio')
            )
            
            # Adicionar personalizações
            for perso in carrinho_item.personalizacoes.all():
                PersonalizacaoItemPedido.objects.create(
                    item_pedido=item_pedido,
                    item_personalizacao=perso.item_personalizacao,
                    opcao_nome=perso.opcao_nome,
                    item_nome=perso.item_nome,
                    preco_adicional=perso.preco_adicional
                )
            
            subtotal_pedido += carrinho_item.subtotal
        
        # Calcular frete
        if pedido.tipo_entrega == 'delivery':
            pedido.taxa_entrega = FreteService.calcular_frete(
                pedido.restaurante, 
                dados_entrega.get('cep', '')
            )
        else:
            pedido.taxa_entrega = Decimal('0.00')
        
        # Calcular totais
        pedido.subtotal = subtotal_pedido
        pedido.total = subtotal_pedido + pedido.taxa_entrega
        pedido.save()
        
        # Criar histórico inicial
        HistoricoStatusPedido.objects.create(
            pedido=pedido,
            status_anterior=None,
            status_novo=pedido.status,
            usuario=usuario
        )
        
        # Limpar carrinho
        carrinho.limpar()
        
        logger.info(f"Pedido criado com sucesso: {pedido}")
        return pedido
    
    @staticmethod
    def _obter_ou_criar_usuario(dados_cliente: Dict[str, Any]) -> Usuario:
        """Obtém usuário existente ou cria novo"""
        celular = dados_cliente['celular']
        email = dados_cliente.get('email', '').strip()
        
        # Tentar por email primeiro
        if email:
            usuario = Usuario.objects.filter(email=email).first()
            if usuario:
                return usuario
        
        # Tentar por celular
        usuario = Usuario.objects.filter(celular=celular).first()
        if usuario:
            return usuario
        
        # Criar novo usuário
        nome_parts = dados_cliente['nome'].split()
        first_name = nome_parts[0]
        last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else ''
        
        # Gerar username único
        base_username = celular.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        username = base_username
        counter = 1
        while Usuario.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        usuario = Usuario.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            celular=celular,
            tipo_usuario='cliente'
        )
        
        logger.info(f"Novo usuário criado: {usuario}")
        return usuario
    
    @staticmethod
    def _adicionar_endereco_entrega(pedido: Pedido, dados_entrega: Dict[str, Any]):
        """Adiciona dados de endereço ao pedido"""
        pedido.endereco_cep = dados_entrega.get('cep', '')
        pedido.endereco_logradouro = dados_entrega.get('logradouro', '')
        pedido.endereco_numero = dados_entrega.get('numero', '')
        pedido.endereco_complemento = dados_entrega.get('complemento', '')
        pedido.endereco_bairro = dados_entrega.get('bairro', '')
        pedido.endereco_cidade = dados_entrega.get('cidade', '')
        pedido.endereco_estado = dados_entrega.get('estado', '')
        pedido.endereco_ponto_referencia = dados_entrega.get('ponto_referencia', '')


class FreteService:
    """Serviço para cálculo de frete"""
    
    @staticmethod
    def calcular_frete(restaurante: Restaurante, cep_destino: str) -> Decimal:
        """
        Calcula o valor do frete baseado nas configurações do restaurante
        """
        try:
            # Se frete fixo está configurado
            if restaurante.frete_fixo and restaurante.valor_frete_fixo is not None:
                return Decimal(str(restaurante.valor_frete_fixo))
            
            # Se não tem configuração de frete, usar taxa padrão
            if restaurante.valor_frete_padrao is None:
                return Decimal('0.00')
            
            valor_base = Decimal(str(restaurante.valor_frete_padrao))
            
            # Se não tem configuração de distância, retornar valor base
            if not restaurante.valor_adicional_km or not cep_destino or not restaurante.cep:
                return valor_base
            
            # Calcular frete por distância usando utilitário existente
            try:
                from .utils_frete_cep import calcular_frete_cep
                
                resultado = calcular_frete_cep(
                    cep_destino=cep_destino,
                    cep_referencia=restaurante.cep,
                    taxa_base=float(restaurante.valor_frete_padrao),
                    taxa_km=float(restaurante.valor_adicional_km),
                    raio_limite_km=float(restaurante.raio_limite_km) if restaurante.raio_limite_km else None
                )
                
                if resultado and 'erro' not in resultado and 'custo_frete' in resultado:
                    return Decimal(str(resultado['custo_frete']))
                else:
                    logger.warning(f"Erro no cálculo de frete: {resultado}")
                    return valor_base
                    
            except ImportError:
                logger.warning("utils_frete_cep não disponível, usando valor base")
                return valor_base
            except Exception as e:
                logger.error(f"Erro ao calcular frete por distância: {e}")
                return valor_base
        
        except Exception as e:
            logger.error(f"Erro no cálculo de frete: {e}")
            return Decimal('0.00')
    
    @staticmethod
    def validar_cep_entrega(restaurante: Restaurante, cep_destino: str) -> Dict[str, Any]:
        """
        Valida se o CEP está dentro da área de entrega
        """
        if not cep_destino or len(cep_destino.replace('-', '').replace(' ', '')) != 8:
            return {'valido': False, 'erro': 'CEP inválido'}
        
        if not restaurante.raio_limite_km:
            return {'valido': True, 'distancia_km': None}
        
        try:
            from .utils_frete_cep import calcular_frete_cep
            
            resultado = calcular_frete_cep(
                cep_destino=cep_destino,
                cep_referencia=restaurante.cep,
                raio_limite_km=float(restaurante.raio_limite_km)
            )
            
            if resultado and 'erro' in resultado:
                return {'valido': False, 'erro': resultado['erro']}
            
            if resultado and 'distancia_km' in resultado:
                distancia = resultado['distancia_km']
                if distancia <= float(restaurante.raio_limite_km):
                    return {'valido': True, 'distancia_km': distancia}
                else:
                    return {
                        'valido': False, 
                        'erro': f'CEP fora da área de entrega. Máximo: {restaurante.raio_limite_km}km'
                    }
            
            return {'valido': True, 'distancia_km': None}
            
        except Exception as e:
            logger.error(f"Erro na validação do CEP: {e}")
            return {'valido': True, 'distancia_km': None}  # Em caso de erro, permite a entrega