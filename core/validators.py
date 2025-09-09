"""
Validadores especializados para o sistema Menuly.
Centraliza todas as validações de negócio reutilizáveis.
"""

import re
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class CarrinhoValidators:
    """Validadores para operações do carrinho"""
    
    @staticmethod
    def validar_quantidade(quantidade: int) -> None:
        """Valida se a quantidade é válida"""
        if not isinstance(quantidade, int):
            raise ValidationError("Quantidade deve ser um número inteiro")
        
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        
        if quantidade > 99:
            raise ValidationError("Quantidade não pode ser maior que 99")
    
    @staticmethod
    def validar_produto_disponivel(produto) -> None:
        """Valida se o produto está disponível"""
        if not produto.disponivel:
            raise ValidationError(f"Produto '{produto.nome}' não está disponível")
        
        if produto.estoque_esgotado:
            raise ValidationError(f"Produto '{produto.nome}' está em falta")
        
        if not produto.categoria.ativo:
            raise ValidationError(f"Categoria do produto '{produto.nome}' está inativa")
        
        if not produto.restaurante.status == 'ativo':
            raise ValidationError("Restaurante não está ativo")
    
    @staticmethod
    def validar_estoque(produto, quantidade: int) -> None:
        """Valida se há estoque suficiente"""
        if not produto.controlar_estoque:
            return
        
        if produto.estoque_atual < quantidade:
            raise ValidationError(
                f"Estoque insuficiente para '{produto.nome}'. "
                f"Disponível: {produto.estoque_atual}, Solicitado: {quantidade}"
            )
    
    @staticmethod
    def validar_personalizacoes(personalizacoes: List[Dict], produto) -> None:
        """Valida personalizações do produto"""
        if not personalizacoes:
            return
        
        opcoes_produto = produto.opcoes_personalizacao.filter(ativo=True)
        opcoes_obrigatorias = opcoes_produto.filter(obrigatorio=True)
        
        # Verificar se todas as opções obrigatórias foram atendidas
        opcoes_fornecidas = set()
        for perso in personalizacoes:
            item_id = perso.get('item_id')
            if not item_id:
                raise ValidationError("ID da personalização é obrigatório")
            
            # Verificar se o item de personalização existe e pertence ao produto
            try:
                from .models import ItemPersonalizacao
                item_personalizacao = ItemPersonalizacao.objects.get(id=item_id)
                if item_personalizacao.opcao.produto != produto:
                    raise ValidationError("Personalização não pertence ao produto")
                
                opcoes_fornecidas.add(item_personalizacao.opcao.id)
                
            except ItemPersonalizacao.DoesNotExist:
                raise ValidationError(f"Personalização não encontrada: {item_id}")
        
        # Verificar opções obrigatórias
        for opcao_obrigatoria in opcoes_obrigatorias:
            if opcao_obrigatoria.id not in opcoes_fornecidas:
                raise ValidationError(f"Opção obrigatória não selecionada: {opcao_obrigatoria.nome}")
    
    @staticmethod
    def validar_meio_a_meio(dados_meio_a_meio: Dict, produto) -> None:
        """Valida dados de pizza meio-a-meio"""
        if not dados_meio_a_meio:
            return
        
        if not produto.permite_meio_a_meio:
            raise ValidationError(f"Produto '{produto.nome}' não permite meio-a-meio")
        
        sabor1 = dados_meio_a_meio.get('sabor1')
        sabor2 = dados_meio_a_meio.get('sabor2')
        
        if not sabor1 or not sabor2:
            raise ValidationError("Dois sabores são obrigatórios para meio-a-meio")
        
        if sabor1 == sabor2:
            raise ValidationError("Os sabores devem ser diferentes para meio-a-meio")


class PedidoValidators:
    """Validadores para criação e gestão de pedidos"""
    
    @staticmethod
    def validar_dados_cliente(dados: Dict[str, Any]) -> None:
        """Valida dados do cliente"""
        nome = dados.get('nome', '').strip()
        if not nome:
            raise ValidationError("Nome do cliente é obrigatório")
        
        if len(nome) < 2:
            raise ValidationError("Nome deve ter pelo menos 2 caracteres")
        
        celular = dados.get('celular', '').strip()
        if not celular:
            raise ValidationError("Celular do cliente é obrigatório")
        
        PedidoValidators.validar_celular(celular)
        
        email = dados.get('email', '').strip()
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError("E-mail inválido")
    
    @staticmethod
    def validar_celular(celular: str) -> None:
        """Valida formato do celular"""
        # Remove caracteres especiais
        celular_limpo = re.sub(r'[^\d+]', '', celular)
        
        # Padrões aceitos: +5511999999999, 5511999999999, 11999999999, 999999999
        patterns = [
            r'^\+55\d{11}$',  # +55 + DDD + 9 dígitos
            r'^55\d{11}$',    # 55 + DDD + 9 dígitos
            r'^\d{11}$',      # DDD + 9 dígitos
            r'^\d{9}$',       # 9 dígitos
        ]
        
        if not any(re.match(pattern, celular_limpo) for pattern in patterns):
            raise ValidationError("Formato de celular inválido")
    
    @staticmethod
    def validar_endereco_entrega(dados: Dict[str, Any]) -> None:
        """Valida dados do endereço de entrega"""
        campos_obrigatorios = ['cep', 'logradouro', 'numero', 'bairro', 'cidade', 'estado']
        
        for campo in campos_obrigatorios:
            valor = dados.get(campo, '').strip()
            if not valor:
                raise ValidationError(f"{campo.replace('_', ' ').title()} é obrigatório")
        
        # Validar CEP
        cep = dados.get('cep', '').replace('-', '').replace(' ', '')
        if len(cep) != 8 or not cep.isdigit():
            raise ValidationError("CEP deve conter 8 dígitos")
        
        # Validar estado (UF)
        estado = dados.get('estado', '').upper()
        ufs_validas = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 
            'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 
            'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        if estado not in ufs_validas:
            raise ValidationError("Estado inválido")
    
    @staticmethod
    def validar_forma_pagamento(forma_pagamento: str, troco_para: Optional[Decimal] = None) -> None:
        """Valida forma de pagamento"""
        formas_validas = ['dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'vale_refeicao', 'online']
        
        if forma_pagamento not in formas_validas:
            raise ValidationError("Forma de pagamento inválida")
        
        # Validar troco para dinheiro
        if forma_pagamento == 'dinheiro' and troco_para is not None:
            if troco_para <= 0:
                raise ValidationError("Valor do troco deve ser maior que zero")
            
            # Validar se troco é maior que o total será feito na view/service
    
    @staticmethod
    def validar_tipo_entrega(tipo_entrega: str) -> None:
        """Valida tipo de entrega"""
        tipos_validos = ['delivery', 'retirada']
        
        if tipo_entrega not in tipos_validos:
            raise ValidationError("Tipo de entrega inválido")
    
    @staticmethod
    def validar_restaurante_ativo(restaurante) -> None:
        """Valida se o restaurante pode receber pedidos"""
        if restaurante.status != 'ativo':
            raise ValidationError("Restaurante não está ativo")
        
        if restaurante.plano_vencido():
            raise ValidationError("Plano do restaurante está vencido")
        
        if not restaurante.pode_processar_pedido():
            raise ValidationError("Restaurante atingiu limite de pedidos do plano")
    
    @staticmethod
    def validar_horario_funcionamento(restaurante) -> None:
        """Valida se o restaurante está aberto"""
        if not restaurante.esta_aberto:
            raise ValidationError("Restaurante está fechado no momento")


class ValidadorEcommerce:
    """Validadores gerais para e-commerce"""
    
    @staticmethod
    def validar_preco(preco: Any) -> Decimal:
        """Valida e converte preço para Decimal"""
        if preco is None:
            raise ValidationError("Preço é obrigatório")
        
        try:
            if isinstance(preco, str):
                preco = preco.replace(',', '.')
            
            preco_decimal = Decimal(str(preco))
            
            if preco_decimal < 0:
                raise ValidationError("Preço não pode ser negativo")
            
            if preco_decimal > Decimal('999999.99'):
                raise ValidationError("Preço muito alto")
            
            return preco_decimal.quantize(Decimal('0.01'))
            
        except (InvalidOperation, ValueError):
            raise ValidationError("Formato de preço inválido")
    
    @staticmethod
    def validar_desconto(valor_desconto: Any, valor_total: Decimal) -> Decimal:
        """Valida desconto aplicado"""
        desconto = ValidadorEcommerce.validar_preco(valor_desconto)
        
        if desconto > valor_total:
            raise ValidationError("Desconto não pode ser maior que o valor total")
        
        return desconto
    
    @staticmethod
    def sanitizar_observacoes(observacoes: str) -> str:
        """Sanitiza e valida observações"""
        if not observacoes:
            return ""
        
        observacoes = observacoes.strip()
        
        if len(observacoes) > 500:
            raise ValidationError("Observações não podem ter mais que 500 caracteres")
        
        # Remover caracteres potencialmente perigosos
        caracteres_perigosos = ['<', '>', '{', '}', '[', ']']
        for char in caracteres_perigosos:
            observacoes = observacoes.replace(char, '')
        
        return observacoes


class ValidadorCEP:
    """Validador especializado para CEPs"""
    
    @staticmethod
    def validar_formato_cep(cep: str) -> str:
        """Valida e normaliza formato do CEP"""
        if not cep:
            raise ValidationError("CEP é obrigatório")
        
        # Remove caracteres especiais
        cep_limpo = re.sub(r'[^\d]', '', cep)
        
        if len(cep_limpo) != 8:
            raise ValidationError("CEP deve conter 8 dígitos")
        
        if not cep_limpo.isdigit():
            raise ValidationError("CEP deve conter apenas números")
        
        return cep_limpo
    
    @staticmethod
    def validar_cep_existe(cep: str) -> bool:
        """Valida se o CEP existe (usando API externa)"""
        try:
            import requests
            response = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return 'erro' not in data
            
            return False
            
        except Exception as e:
            logger.warning(f"Erro ao validar CEP {cep}: {e}")
            # Em caso de erro na API, assumimos que é válido para não bloquear pedidos
            return True


class ValidadorSeguranca:
    """Validadores de segurança"""
    
    @staticmethod
    def validar_sql_injection(valor: str) -> None:
        """Valida contra SQL injection básico"""
        if not isinstance(valor, str):
            return
        
        palavras_suspeitas = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'SELECT', 
            'UNION', 'EXEC', 'SCRIPT', '--', ';',
            'xp_', 'sp_', 'exec(', 'eval('
        ]
        
        valor_upper = valor.upper()
        for palavra in palavras_suspeitas:
            if palavra in valor_upper:
                raise ValidationError("Conteúdo não permitido detectado")
    
    @staticmethod
    def validar_xss(valor: str) -> None:
        """Valida contra XSS básico"""
        if not isinstance(valor, str):
            return
        
        padroes_suspeitos = [
            r'<script',
            r'javascript:',
            r'onclick=',
            r'onerror=',
            r'onload=',
        ]
        
        valor_lower = valor.lower()
        for padrao in padroes_suspeitos:
            if re.search(padrao, valor_lower):
                raise ValidationError("Conteúdo não permitido detectado")
    
    @staticmethod
    def validar_entrada_usuario(valor: str) -> str:
        """Validação geral para entradas de usuário"""
        if not valor:
            return ""
        
        ValidadorSeguranca.validar_sql_injection(valor)
        ValidadorSeguranca.validar_xss(valor)
        
        return valor.strip()