# ==================== VIEWS DE SUPORTE E AJUDA ====================

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .utils import painel_loja_required
from django import forms
import json

class TicketSuporteForm(forms.Form):
    """Form para criar ticket de suporte"""
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    CATEGORIA_CHOICES = [
        ('tecnico', 'Problema Técnico'),
        ('financeiro', 'Questão Financeira'),
        ('produto', 'Problemas com Produtos'),
        ('pedido', 'Problemas com Pedidos'),
        ('configuracao', 'Configuração da Loja'),
        ('outro', 'Outro'),
    ]
    
    assunto = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descreva brevemente o problema'
        }),
        label='Assunto'
    )
    
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Categoria'
    )
    
    prioridade = forms.ChoiceField(
        choices=PRIORIDADE_CHOICES,
        initial='media',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Prioridade'
    )
    
    descricao = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Descreva detalhadamente o problema, incluindo passos para reproduzi-lo se aplicável'
        }),
        label='Descrição Detalhada'
    )
    
    email_contato = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        }),
        label='Email para Contato',
        help_text='Email onde você gostaria de receber a resposta'
    )

@painel_loja_required
def suporte_index(request):
    """Página principal de suporte e ajuda"""
    
    # FAQ data
    faq_data = [
        {
            'categoria': 'Primeiros Passos',
            'perguntas': [
                {
                    'pergunta': 'Como configurar minha loja pela primeira vez?',
                    'resposta': 'Vá em "Personalizar Loja" no menu lateral e configure o logo, banner, cores e informações básicas da sua loja. Depois configure o frete em "Configurar Frete".'
                },
                {
                    'pergunta': 'Como adicionar produtos ao meu cardápio?',
                    'resposta': 'Primeiro crie categorias em "Cardápio > Categorias", depois adicione produtos em "Cardápio > Produtos". Cada produto deve ter nome, descrição, preço e categoria.'
                },
                {
                    'pergunta': 'Como gerenciar minha equipe?',
                    'resposta': 'Use o menu "Equipe" para adicionar gerentes e atendentes. Cada tipo de usuário tem permissões específicas no sistema.'
                }
            ]
        },
        {
            'categoria': 'Gestão de Pedidos',
            'perguntas': [
                {
                    'pergunta': 'Como acompanhar os pedidos em tempo real?',
                    'resposta': 'Use a página "Pedidos" que mostra todos os pedidos organizados por status (Novo, Em Preparo, Pronto, etc.). Você pode avançar o status clicando nos botões.'
                },
                {
                    'pergunta': 'Como imprimir cupons dos pedidos?',
                    'resposta': 'Na página de pedidos, clique em "Cupom" ao lado de cada pedido para visualizar e imprimir o cupom com os detalhes do pedido.'
                },
                {
                    'pergunta': 'Como configurar impressoras?',
                    'resposta': 'Vá em "Impressoras" no menu e configure suas impressoras por IP, USB ou Bluetooth. Você pode ter impressoras diferentes para cozinha e balcão.'
                }
            ]
        },
        {
            'categoria': 'Problemas Técnicos',
            'perguntas': [
                {
                    'pergunta': 'Não consigo fazer login no painel',
                    'resposta': 'Verifique se está usando o email correto como usuário. Se esqueceu a senha, entre em contato com o suporte. Certifique-se de que tem permissão para acessar o painel.'
                },
                {
                    'pergunta': 'Os pedidos não estão aparecendo',
                    'resposta': 'Verifique se você está logado com o usuário correto e se tem permissão para ver os pedidos do restaurante. Atendentes só veem pedidos dos restaurantes onde trabalham.'
                },
                {
                    'pergunta': 'Erro ao alterar status do pedido',
                    'resposta': 'Certifique-se de que tem permissão para gerenciar pedidos. Se o erro persistir, recarregue a página e tente novamente.'
                }
            ]
        }
    ]
    
    # Tutoriais data
    tutoriais_data = [
        {
            'titulo': 'Configuração Inicial da Loja',
            'descricao': 'Aprenda a configurar sua loja do zero',
            'duracao': '5 min',
            'passos': [
                'Acesse "Personalizar Loja" no menu lateral',
                'Faça upload do logo e banner da sua loja',
                'Configure as cores principais da loja',
                'Defina os horários de funcionamento',
                'Configure informações de contato'
            ]
        },
        {
            'titulo': 'Criando seu Primeiro Cardápio',
            'descricao': 'Como organizar produtos e categorias',
            'duracao': '8 min',
            'passos': [
                'Vá em "Cardápio > Categorias"',
                'Crie categorias (ex: Lanches, Bebidas, Sobremesas)',
                'Vá em "Cardápio > Produtos"',
                'Adicione produtos com fotos, preços e descrições',
                'Organize a ordem das categorias e produtos'
            ]
        },
        {
            'titulo': 'Gerenciando Pedidos',
            'descricao': 'Fluxo completo de atendimento',
            'duracao': '6 min',
            'passos': [
                'Monitore novos pedidos na página "Pedidos"',
                'Clique em "Iniciar Preparo" para pedidos novos',
                'Marque como "Pronto" quando terminar o preparo',
                'Use "Saiu para Entrega" para delivery',
                'Finalize o pedido após a entrega'
            ]
        },
        {
            'titulo': 'Configurando Impressoras',
            'descricao': 'Setup de impressoras térmicas',
            'duracao': '10 min',
            'passos': [
                'Vá em "Impressoras" no menu',
                'Clique em "Cadastrar Impressora"',
                'Configure o tipo de conexão (IP, USB, etc.)',
                'Teste a impressora com o botão "Testar"',
                'Configure impressoras específicas por tipo de pedido'
            ]
        }
    ]
    
    context = {
        'faq_data': faq_data,
        'tutoriais_data': tutoriais_data,
    }
    
    return render(request, 'admin_loja/suporte_index.html', context)

@painel_loja_required
def suporte_contato(request):
    """Página para enviar ticket de suporte"""
    
    if request.method == 'POST':
        form = TicketSuporteForm(request.POST)
        if form.is_valid():
            # Aqui você pode salvar o ticket no banco de dados
            # Por enquanto vamos simular o envio
            
            ticket_data = {
                'usuario': request.user.username,
                'usuario_email': request.user.email,
                'assunto': form.cleaned_data['assunto'],
                'categoria': form.cleaned_data['categoria'],
                'prioridade': form.cleaned_data['prioridade'],
                'descricao': form.cleaned_data['descricao'],
                'email_contato': form.cleaned_data['email_contato'],
                'data_criacao': timezone.now().isoformat(),
            }
            
            # Simular envio do ticket (aqui você integraria com seu sistema de tickets)
            print(f"TICKET DE SUPORTE CRIADO: {json.dumps(ticket_data, indent=2)}")
            
            messages.success(request, 
                f'Ticket de suporte criado com sucesso! '
                f'Você receberá uma resposta em até 24 horas no email: {form.cleaned_data["email_contato"]}')
            
            return redirect('admin_loja:suporte_index')
    else:
        # Pré-preencher com email do usuário
        initial_data = {
            'email_contato': request.user.email
        }
        form = TicketSuporteForm(initial=initial_data)
    
    return render(request, 'admin_loja/suporte_contato.html', {
        'form': form
    })

@painel_loja_required
def suporte_chat_api(request):
    """API para chat de suporte (simulado)"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensagem = data.get('mensagem', '').strip()
            
            if not mensagem:
                return JsonResponse({'success': False, 'error': 'Mensagem não pode estar vazia'})
            
            # Simular resposta automática do suporte
            respostas_automaticas = {
                'ola': 'Olá! Como posso ajudá-lo hoje?',
                'pedido': 'Para problemas com pedidos, verifique a página "Pedidos" no menu lateral.',
                'impressora': 'Para configurar impressoras, acesse "Impressoras" no menu e siga o tutorial.',
                'login': 'Se está com problemas de login, verifique se está usando o email correto como usuário.',
                'produto': 'Para gerenciar produtos, vá em "Cardápio > Produtos" no menu lateral.',
                'ajuda': 'Consulte nossa seção de FAQ ou envie um ticket de suporte para ajuda personalizada.',
            }
            
            # Encontrar resposta baseada em palavras-chave
            resposta = 'Obrigado pela sua mensagem! Nossa equipe analisará sua solicitação. Para respostas mais rápidas, consulte nossa FAQ ou envie um ticket de suporte.'
            
            for palavra_chave, resposta_auto in respostas_automaticas.items():
                if palavra_chave.lower() in mensagem.lower():
                    resposta = resposta_auto
                    break
            
            return JsonResponse({
                'success': True,
                'resposta': resposta,
                'timestamp': timezone.now().strftime('%H:%M')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Dados inválidos'})
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'})