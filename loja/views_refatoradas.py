"""
Exemplo de views refatoradas usando a nova arquitetura com Services.
Demonstra como o código fica mais limpo, testável e escalável.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

from core.models import Restaurante, Produto, Carrinho
from core.services import CarrinhoService, PedidoService, FreteService
from core.serializers import (
    CarrinhoSerializer, AdicionarItemCarrinhoSerializer,
    CriarPedidoSerializer, PedidoSerializer, CalcularFreteSerializer,
    FreteResponseSerializer, ErroAPISerializer, SucessoAPISerializer
)
from .views import BaseLojaView

logger = logging.getLogger(__name__)


class CarrinhoViewRefatorada(BaseLojaView):
    """Versão refatorada da view do carrinho usando CarrinhoService"""
    template_name = 'loja/carrinho.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obter carrinho usando service
            carrinho = CarrinhoService.obter_carrinho(
                usuario=self.request.user if self.request.user.is_authenticated else None,
                sessao_id=self.request.session.session_key,
                restaurante=context['restaurante']
            )
            
            # Calcular resumo do carrinho
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            # Calcular frete se houver endereço
            taxa_entrega = 0
            if not resumo['carrinho_vazio'] and self.request.session.get('endereco_entrega'):
                taxa_entrega = FreteService.calcular_frete(
                    context['restaurante'], 
                    self.request.session.get('endereco_entrega', {}).get('cep', '')
                )
            
            context.update({
                'carrinho': carrinho,
                'itens_carrinho': resumo['itens'],
                'total_carrinho': resumo['subtotal'],
                'taxa_entrega': taxa_entrega,
                'total_final': resumo['subtotal'] + taxa_entrega,
                'carrinho_count': resumo['total_itens'],
            })
            
        except Exception as e:
            logger.error(f"Erro ao carregar carrinho: {e}")
            messages.error(self.request, 'Erro ao carregar carrinho')
            context.update({
                'itens_carrinho': [],
                'total_carrinho': 0,
                'carrinho_count': 0,
            })
        
        return context


class CheckoutViewRefatorada(BaseLojaView):
    """Versão refatorada da view do checkout"""
    template_name = 'loja/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=self.request.user if self.request.user.is_authenticated else None,
                sessao_id=self.request.session.session_key,
                restaurante=context['restaurante']
            )
            
            if carrinho.esta_vazio():
                messages.warning(self.request, 'Seu carrinho está vazio')
                return context
            
            # Calcular resumo
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            # Taxa de entrega (será calculada dinamicamente no frontend)
            taxa_entrega = 0
            
            context.update({
                'carrinho': carrinho,
                'itens_carrinho': resumo['itens'],
                'total_carrinho': resumo['subtotal'],
                'taxa_entrega': taxa_entrega,
                'total_final': resumo['subtotal'] + taxa_entrega,
                'carrinho_count': resumo['total_itens'],
            })
            
            # Endereços do usuário se logado
            if self.request.user.is_authenticated:
                context['enderecos_usuario'] = self.request.user.enderecos.all()
            
            # Formas de pagamento
            context['formas_pagamento'] = [
                ('dinheiro', 'Dinheiro'),
                ('cartao_credito', 'Cartão de Crédito'),
                ('cartao_debito', 'Cartão de Débito'),
                ('pix', 'PIX'),
            ]
            
        except Exception as e:
            logger.error(f"Erro no checkout: {e}")
            messages.error(self.request, 'Erro ao carregar checkout')
            return redirect('loja:carrinho', restaurante_slug=kwargs.get('restaurante_slug'))
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Processa o pedido usando PedidoService"""
        try:
            # Obter restaurante
            restaurante_slug = kwargs.get('restaurante_slug')
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
            
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            if carrinho.esta_vazio():
                messages.error(request, 'Seu carrinho está vazio')
                return redirect('loja:carrinho', restaurante_slug=restaurante_slug)
            
            # Preparar dados do pedido
            dados_cliente = {
                'nome': request.POST.get('nome', '').strip(),
                'celular': request.POST.get('celular', '').strip(),
                'email': request.POST.get('email', '').strip(),
            }
            
            dados_entrega = {
                'tipo': request.POST.get('tipo_entrega', 'delivery'),
            }
            
            # Dados de endereço se delivery
            if dados_entrega['tipo'] == 'delivery':
                dados_entrega.update({
                    'cep': request.POST.get('cep', '').strip(),
                    'logradouro': request.POST.get('logradouro', '').strip(),
                    'numero': request.POST.get('numero', '').strip(),
                    'complemento': request.POST.get('complemento', '').strip(),
                    'bairro': request.POST.get('bairro', '').strip(),
                    'cidade': request.POST.get('cidade', '').strip(),
                    'estado': request.POST.get('estado', '').strip(),
                    'ponto_referencia': request.POST.get('ponto_referencia', '').strip(),
                })
            
            forma_pagamento = request.POST.get('forma_pagamento')
            observacoes = request.POST.get('observacoes', '').strip()
            
            # Troco se pagamento em dinheiro
            troco_para = None
            if forma_pagamento == 'dinheiro':
                troco_str = request.POST.get('troco_para', '0').replace(',', '.')
                if troco_str:
                    try:
                        from decimal import Decimal
                        troco_para = Decimal(troco_str)
                    except:
                        messages.error(request, 'Valor de troco inválido')
                        return self.get(request, *args, **kwargs)
            
            # Criar pedido usando service
            with transaction.atomic():
                pedido = PedidoService.criar_pedido_do_carrinho(
                    carrinho=carrinho,
                    dados_cliente=dados_cliente,
                    dados_entrega=dados_entrega,
                    forma_pagamento=forma_pagamento,
                    observacoes=observacoes,
                    troco_para=troco_para
                )
            
            # Salvar ID do pedido na sessão para confirmação
            request.session['ultimo_pedido_id'] = str(pedido.id)
            
            messages.success(request, f'Pedido #{pedido.numero} criado com sucesso!')
            return redirect('loja:confirmacao_pedido', restaurante_slug=restaurante_slug)
            
        except ValidationError as e:
            messages.error(request, str(e))
            return self.get(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Erro ao processar pedido: {e}")
            messages.error(request, 'Erro interno. Tente novamente.')
            return self.get(request, *args, **kwargs)


# ======================= APIs REST =======================

class CarrinhoAPIView(APIView):
    """API para gestão do carrinho"""
    
    def get(self, request, restaurante_slug):
        """Retorna o carrinho atual"""
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            serializer = CarrinhoSerializer(carrinho)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Erro ao obter carrinho: {e}")
            return Response(
                {'erro': 'Erro ao carregar carrinho'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, restaurante_slug):
        """Adiciona item ao carrinho"""
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            serializer = AdicionarItemCarrinhoSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'erro': 'Dados inválidos', 'detalhes': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            # Obter produto
            produto = get_object_or_404(Produto, id=serializer.validated_data['produto_id'])
            
            # Adicionar item
            item = CarrinhoService.adicionar_item(
                carrinho=carrinho,
                produto=produto,
                quantidade=serializer.validated_data['quantidade'],
                observacoes=serializer.validated_data.get('observacoes', ''),
                personalizacoes=serializer.validated_data.get('personalizacoes', []),
                dados_meio_a_meio=serializer.validated_data.get('dados_meio_a_meio')
            )
            
            # Retornar resumo atualizado
            resumo = CarrinhoService.calcular_resumo(carrinho)
            
            return Response({
                'sucesso': True,
                'mensagem': 'Item adicionado ao carrinho',
                'dados': {
                    'item_id': str(item.id),
                    'total_itens': resumo['total_itens'],
                    'subtotal': resumo['subtotal']
                }
            })
            
        except ValidationError as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar item ao carrinho: {e}")
            return Response(
                {'erro': 'Erro interno'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, restaurante_slug):
        """Limpa o carrinho"""
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            CarrinhoService.limpar_carrinho(carrinho)
            
            return Response({
                'sucesso': True,
                'mensagem': 'Carrinho limpo com sucesso'
            })
            
        except Exception as e:
            logger.error(f"Erro ao limpar carrinho: {e}")
            return Response(
                {'erro': 'Erro ao limpar carrinho'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CalcularFreteAPIView(APIView):
    """API para calcular frete"""
    
    def post(self, request, restaurante_slug):
        """Calcula o frete para um CEP"""
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            serializer = CalcularFreteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'erro': 'CEP inválido', 'detalhes': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cep = serializer.validated_data['cep']
            
            # Validar área de entrega
            validacao = FreteService.validar_cep_entrega(restaurante, cep)
            if not validacao['valido']:
                return Response(
                    {'erro': validacao['erro']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calcular frete
            valor_frete = FreteService.calcular_frete(restaurante, cep)
            
            response_data = {
                'valor_frete': valor_frete,
                'tempo_estimado_min': restaurante.tempo_entrega_min,
                'tempo_estimado_max': restaurante.tempo_entrega_max,
                'area_entrega_valida': validacao['valido'],
            }
            
            if validacao.get('distancia_km'):
                response_data['distancia_km'] = validacao['distancia_km']
            
            response_serializer = FreteResponseSerializer(response_data)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Erro ao calcular frete: {e}")
            return Response(
                {'erro': 'Erro ao calcular frete'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CriarPedidoAPIView(APIView):
    """API para criar pedido do carrinho"""
    
    def post(self, request, restaurante_slug):
        """Cria um pedido a partir do carrinho"""
        try:
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            serializer = CriarPedidoSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'erro': 'Dados inválidos', 'detalhes': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obter carrinho
            carrinho = CarrinhoService.obter_carrinho(
                usuario=request.user if request.user.is_authenticated else None,
                sessao_id=request.session.session_key,
                restaurante=restaurante
            )
            
            if carrinho.esta_vazio():
                return Response(
                    {'erro': 'Carrinho está vazio'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Criar pedido
            with transaction.atomic():
                pedido = PedidoService.criar_pedido_do_carrinho(
                    carrinho=carrinho,
                    dados_cliente=serializer.validated_data['dados_cliente'],
                    dados_entrega=serializer.validated_data['dados_entrega'],
                    forma_pagamento=serializer.validated_data['forma_pagamento'],
                    observacoes=serializer.validated_data.get('observacoes', ''),
                    troco_para=serializer.validated_data.get('troco_para')
                )
            
            # Retornar dados do pedido
            pedido_serializer = PedidoSerializer(pedido)
            
            return Response({
                'sucesso': True,
                'mensagem': f'Pedido #{pedido.numero} criado com sucesso',
                'dados': {
                    'pedido': pedido_serializer.data,
                    'redirect_url': f'/loja/{restaurante_slug}/confirmacao-pedido/'
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(
                {'erro': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erro ao criar pedido: {e}")
            return Response(
                {'erro': 'Erro interno'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )