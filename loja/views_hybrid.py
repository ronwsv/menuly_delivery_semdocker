"""
Views Híbridas - Migração Gradual
Permite coexistência entre sistema antigo e novo sem impacto no usuário
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
import json
import logging

from core.models import Restaurante, Produto
from core.carrinho_hybrid import CarrinhoHybridService
from core.services import FreteService
from .views import BaseLojaView

logger = logging.getLogger(__name__)


class CarrinhoViewHybrid(BaseLojaView):
    """
    View híbrida do carrinho que funciona com ambos os sistemas
    Substitua a CarrinhoView original por esta
    """
    template_name = 'loja/carrinho.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Usar sistema híbrido
            resumo = CarrinhoHybridService.calcular_resumo_hybrid(
                self.request, context['restaurante']
            )
            
            # Calcular frete se houver endereço
            taxa_entrega = 0
            if not resumo['carrinho_vazio'] and self.request.session.get('endereco_entrega'):
                taxa_entrega = FreteService.calcular_frete(
                    context['restaurante'], 
                    self.request.session.get('endereco_entrega', {}).get('cep', '')
                )
            
            context.update({
                'itens_carrinho': resumo['itens'],
                'total_carrinho': resumo['subtotal'],
                'taxa_entrega': taxa_entrega,
                'total_final': resumo['subtotal'] + taxa_entrega,
                'carrinho_count': resumo['total_itens'],
                'total_items': len(resumo['itens']),
            })
            
            logger.info(f"Carrinho carregado: {resumo['total_itens']} itens")
            
        except Exception as e:
            logger.error(f"Erro ao carregar carrinho híbrido: {e}")
            messages.error(self.request, 'Erro ao carregar carrinho')
            context.update({
                'itens_carrinho': [],
                'total_carrinho': 0,
                'carrinho_count': 0,
                'total_items': 0,
            })
        
        return context


class AdicionarProdutoCarrinhoViewHybrid(View):
    """
    View híbrida para adicionar produtos ao carrinho
    Substitua a view original por esta
    """
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            produto_id = data.get('produto_id')
            quantidade = data.get('quantidade', 1)
            observacoes = data.get('observacoes', '')
            personalizacoes = data.get('personalizacoes', [])
            dados_meio_a_meio = data.get('dados_meio_a_meio')
            
            if not produto_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID do produto é obrigatório'
                }, status=400)
            
            # Obter produto
            try:
                produto = Produto.objects.get(id=produto_id)
            except Produto.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Produto não encontrado'
                }, status=404)
            
            # Obter restaurante
            restaurante_slug = kwargs.get('restaurante_slug')
            if not restaurante_slug:
                return JsonResponse({
                    'success': False,
                    'error': 'Restaurante não identificado'
                }, status=400)
            
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            # Adicionar item usando sistema híbrido
            CarrinhoHybridService.adicionar_item_hybrid(
                request=request,
                restaurante=restaurante,
                produto=produto,
                quantidade=quantidade,
                observacoes=observacoes,
                personalizacoes=personalizacoes,
                dados_meio_a_meio=dados_meio_a_meio
            )
            
            # Calcular novo resumo
            resumo = CarrinhoHybridService.calcular_resumo_hybrid(request, restaurante)
            
            return JsonResponse({
                'success': True,
                'message': 'Produto adicionado ao carrinho!',
                'carrinho_count': resumo['total_itens'],
                'total_valor': float(resumo['subtotal'])
            })
            
        except Exception as e:
            logger.error(f"Erro ao adicionar produto ao carrinho híbrido: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Erro ao adicionar produto: {str(e)}'
            }, status=500)


class CheckoutViewHybrid(BaseLojaView):
    """
    View híbrida do checkout que funciona com ambos os sistemas
    """
    template_name = 'loja/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Usar sistema híbrido
            resumo = CarrinhoHybridService.calcular_resumo_hybrid(
                self.request, context['restaurante']
            )
            
            if resumo['carrinho_vazio']:
                messages.warning(self.request, 'Seu carrinho está vazio')
                return context
            
            context.update({
                'itens_carrinho': resumo['itens'],
                'total_carrinho': resumo['subtotal'],
                'taxa_entrega': 0,  # Calculado dinamicamente no frontend
                'total_final': resumo['subtotal'],
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
            logger.error(f"Erro no checkout híbrido: {e}")
            messages.error(self.request, 'Erro ao carregar checkout')
            return redirect('loja:carrinho', restaurante_slug=kwargs.get('restaurante_slug'))
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Processa pedido usando sistema híbrido
        Por enquanto usa a lógica original, mas preparado para usar PedidoService
        """
        restaurante_slug = kwargs.get('restaurante_slug')
        restaurante = get_object_or_404(Restaurante, slug=restaurante_slug, status='ativo')
        
        try:
            # Verificar se tem carrinho
            resumo = CarrinhoHybridService.calcular_resumo_hybrid(request, restaurante)
            
            if resumo['carrinho_vazio']:
                messages.error(request, 'Seu carrinho está vazio')
                return redirect('loja:carrinho', restaurante_slug=restaurante_slug)
            
            # Por enquanto, redirecionar para processamento original
            # Aqui você pode implementar gradualmente o PedidoService
            
            # Salvar dados do carrinho na sessão para processamento
            request.session['carrinho_para_checkout'] = {
                'itens': [
                    {
                        'produto_id': item['produto']['id'],
                        'nome': item['produto']['nome'],
                        'quantidade': item['quantidade'],
                        'preco': float(item['preco_unitario']),
                        'observacoes': item['observacoes'],
                        'personalizacoes': item['personalizacoes'],
                        'meio_a_meio': item.get('eh_meio_a_meio', False)
                    }
                    for item in resumo['itens']
                ],
                'subtotal': float(resumo['subtotal']),
                'total_itens': resumo['total_itens']
            }
            
            messages.info(request, 'Processando pedido com sistema híbrido...')
            
            # Por enquanto, usar a view original de checkout
            # Depois você pode implementar PedidoService aqui
            from .views import CheckoutView
            checkout_original = CheckoutView()
            checkout_original.request = request
            return checkout_original.post(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Erro ao processar pedido híbrido: {e}")
            messages.error(request, 'Erro interno. Tente novamente.')
            return self.get(request, *args, **kwargs)


class LimparCarrinhoViewHybrid(View):
    """
    View para limpar carrinho usando sistema híbrido
    """
    
    def post(self, request, *args, **kwargs):
        try:
            restaurante_slug = kwargs.get('restaurante_slug')
            restaurante = get_object_or_404(Restaurante, slug=restaurante_slug)
            
            # Obter carrinho ativo
            carrinho_info = CarrinhoHybridService.obter_carrinho_ativo(request, restaurante)
            
            if carrinho_info['tipo'] == 'sessao':
                # Limpar carrinho da sessão
                request.session['carrinho'] = {}
                request.session.modified = True
            else:
                # Limpar carrinho persistente
                from core.services import CarrinhoService
                CarrinhoService.limpar_carrinho(carrinho_info['carrinho'])
            
            return JsonResponse({
                'success': True,
                'message': 'Carrinho limpo com sucesso'
            })
            
        except Exception as e:
            logger.error(f"Erro ao limpar carrinho híbrido: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Erro ao limpar carrinho'
            }, status=500)


# Função helper para facilitar a migração
def substituir_views_gradualmente():
    """
    Guia para substituir views gradualmente:
    
    1. Substitua uma view de cada vez
    2. Teste cada substituição
    3. Monitore logs para verificar se migração está funcionando
    
    ORDEM RECOMENDADA:
    1. CarrinhoView → CarrinhoViewHybrid
    2. AdicionarProdutoCarrinhoView → AdicionarProdutoCarrinhoViewHybrid  
    3. CheckoutView → CheckoutViewHybrid
    4. Views de remoção/alteração de itens
    """
    pass