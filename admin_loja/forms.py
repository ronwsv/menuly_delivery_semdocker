from django import forms
from django.db import models
from core.models import Restaurante, Categoria, Produto, HorarioFuncionamento, Usuario
from .models import Impressora
from django.contrib.auth.models import Group
from django.contrib.auth.forms import PasswordChangeForm


class LogoForm(forms.ModelForm):
    class Meta:
        model = Restaurante
        fields = ['logo']

class BannerForm(forms.ModelForm):
    class Meta:
        model = Restaurante
        fields = ['banner']

class ImpressoraForm(forms.ModelForm):
    class Meta:
        model = Impressora
        fields = [
            'nome', 'tipo_conexao', 'ip_address', 'porta', 
            'caminho_usb', 'ativa', 'padrao_para_tipo',
            'largura_papel', 'cortar_papel'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Impressora Cozinha'}),
            'tipo_conexao': forms.Select(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 192.168.1.100'}),
            'porta': forms.NumberInput(attrs={'class': 'form-control'}),
            'caminho_usb': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: /dev/usb/lp0'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'padrao_para_tipo': forms.Select(attrs={'class': 'form-control'}),
            'largura_papel': forms.NumberInput(attrs={'class': 'form-control'}),
            'cortar_papel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ip_address'].required = False
        self.fields['caminho_usb'].required = False
        self.fields['padrao_para_tipo'].required = False
        
        # Adicionar classes CSS para melhor apresentação
        for field_name, field in self.fields.items():
            if field_name not in ['ativa', 'cortar_papel']:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_conexao = cleaned_data.get('tipo_conexao')
        ip_address = cleaned_data.get('ip_address')
        caminho_usb = cleaned_data.get('caminho_usb')
        
        # Validar campos obrigatórios baseado no tipo de conexão
        if tipo_conexao in ['rede', 'wifi'] and not ip_address:
            raise forms.ValidationError('IP é obrigatório para conexões de rede e Wi-Fi.')
        
        if tipo_conexao == 'usb' and not caminho_usb:
            raise forms.ValidationError('Caminho USB é obrigatório para conexões USB.')
        
        return cleaned_data


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao', 'imagem', 'ordem', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Pizzas, Hambúrgueres, Bebidas'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Descrição da categoria (opcional)'
            }),
            'imagem': forms.FileInput(attrs={'class': 'form-control-file'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.fields['imagem'].required = False
        
        # Se é uma nova categoria, definir ordem automaticamente
        if not self.instance.pk:
            from core.models import Categoria
            last_order = Categoria.objects.aggregate(
                models.Max('ordem')
            )['ordem__max'] or 0
            self.fields['ordem'].initial = last_order + 1


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome', 'descricao', 'categoria', 'preco', 'preco_promocional',
            'imagem_principal', 'destaque', 'disponivel', 'permite_observacoes',
            'tempo_preparo', 'calorias', 'ingredientes', 'alergicos', 'ordem',
            'controlar_estoque', 'estoque_atual', 'estoque_minimo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Pizza Margherita'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva o produto...'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'preco_promocional': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'imagem_principal': forms.FileInput(attrs={'class': 'form-control-file'}),
            'destaque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'disponivel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permite_observacoes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tempo_preparo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'calorias': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'ingredientes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Liste os ingredientes principais...'
            }),
            'alergicos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Informações sobre alérgenos...'
            }),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'controlar_estoque': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'estoque_atual': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        restaurante = kwargs.pop('restaurante', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar categorias pelo restaurante
        if restaurante:
            self.fields['categoria'].queryset = Categoria.objects.filter(
                restaurante=restaurante, ativo=True
            ).order_by('ordem', 'nome')
        
        # Campos opcionais
        optional_fields = [
            'preco_promocional', 'calorias', 'ingredientes', 
            'alergicos', 'imagem_principal', 'estoque_atual', 'estoque_minimo'
        ]
        for field_name in optional_fields:
            self.fields[field_name].required = False
        
        # Se é um novo produto, definir ordem automaticamente
        if not self.instance.pk and restaurante:
            from core.models import Produto
            last_order = Produto.objects.filter(
                restaurante=restaurante
            ).aggregate(
                models.Max('ordem')
            )['ordem__max'] or 0
            self.fields['ordem'].initial = last_order + 1
    
    def clean(self):
        cleaned_data = super().clean()
        preco = cleaned_data.get('preco')
        preco_promocional = cleaned_data.get('preco_promocional')
        controlar_estoque = cleaned_data.get('controlar_estoque')
        estoque_atual = cleaned_data.get('estoque_atual')
        estoque_minimo = cleaned_data.get('estoque_minimo')
        
        if preco_promocional and preco_promocional >= preco:
            raise forms.ValidationError(
                'Preço promocional deve ser menor que o preço normal.'
            )
        
        # Validar campos de estoque se controle de estoque estiver habilitado
        if controlar_estoque:
            if estoque_atual is None:
                self.add_error('estoque_atual', 'Este campo é obrigatório quando controle de estoque está ativado.')
            if estoque_minimo is None:
                self.add_error('estoque_minimo', 'Este campo é obrigatório quando controle de estoque está ativado.')
        
        return cleaned_data


# ==================== FORMS DE PERSONALIZAÇÃO AVANÇADA ====================

class PersonalizacaoVisulaForm(forms.ModelForm):
    """Form para personalização visual da loja"""
    class Meta:
        model = Restaurante
        fields = [
            'slogan', 'mensagem_boas_vindas', 'cor_primaria', 
            'cor_secundaria', 'cor_destaque', 'favicon'
        ]
        widgets = {
            'slogan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A melhor pizza da cidade!'
            }),
            'mensagem_boas_vindas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mensagem de boas-vindas para seus clientes...'
            }),
            'cor_primaria': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'title': 'Escolher cor primária'
            }),
            'cor_secundaria': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'title': 'Escolher cor secundária'
            }),
            'cor_destaque': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color',
                'title': 'Escolher cor de destaque'
            }),
            'favicon': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['favicon'].required = False
        self.fields['slogan'].required = False
        self.fields['mensagem_boas_vindas'].required = False


class HorarioFuncionamentoForm(forms.ModelForm):
    """Form para horários de funcionamento"""
    class Meta:
        model = HorarioFuncionamento
        fields = ['dia_semana', 'hora_abertura', 'hora_fechamento', 'ativo']
        widgets = {
            'dia_semana': forms.Select(attrs={'class': 'form-control'}),
            'hora_abertura': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'hora_fechamento': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        hora_abertura = cleaned_data.get('hora_abertura')
        hora_fechamento = cleaned_data.get('hora_fechamento')
        
        if hora_abertura and hora_fechamento:
            if hora_abertura >= hora_fechamento:
                raise forms.ValidationError(
                    'Horário de abertura deve ser anterior ao horário de fechamento.'
                )
        
        return cleaned_data


# Formset para gerenciar múltiplos horários
HorarioFuncionamentoFormSet = forms.modelformset_factory(
    HorarioFuncionamento,
    form=HorarioFuncionamentoForm,
    extra=0,
    can_delete=True,
    fields=['dia_semana', 'hora_abertura', 'hora_fechamento', 'ativo']
)


class FuncionarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, label="Senha")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False, label="Confirmar Senha")
    
    # Campo para selecionar o grupo (cargo)
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=['Gerente', 'Atendente']),
        empty_label="Selecione um cargo",
        label="Cargo",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'celular', 'password', 'grupo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(99) 99999-9999'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se for edição, preencher o campo grupo com o grupo atual do usuário
        if self.instance.pk:
            try:
                self.fields['grupo'].initial = self.instance.groups.get()
            except Group.DoesNotExist:
                self.fields['grupo'].initial = None
            
            # Senha não é obrigatória na edição
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
        else:
            # Senha é obrigatória na criação
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def clean_celular(self):
        celular = self.cleaned_data.get('celular')
        if celular and Usuario.objects.filter(celular=celular).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este celular já está em uso.")
        return celular

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and password != confirm_password:
            self.add_error('confirm_password', "As senhas não coincidem.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        
        if password:
            user.set_password(password)
        
        user.tipo_usuario = 'funcionario' # Define o tipo de usuário como funcionário
        
        if commit:
            user.save()
            # A atribuição de grupos será feita na view para evitar duplicação
            
        return user


# ==================== FORMS PARA PERFIL DO USUÁRIO ====================

class PerfilForm(forms.ModelForm):
    """Form para editar dados do perfil do usuário"""
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'celular', 'data_nascimento', 'cpf']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999'
            }),
            'data_nascimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00'
            }),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
            'celular': 'Celular',
            'data_nascimento': 'Data de Nascimento',
            'cpf': 'CPF',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este email já está em uso.")
        return email

    def clean_celular(self):
        celular = self.cleaned_data.get('celular')
        if celular and Usuario.objects.filter(celular=celular).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este celular já está em uso.")
        return celular


class AlterarSenhaForm(PasswordChangeForm):
    """Form customizado para alterar senha"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Senha atual'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nova senha'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar nova senha'
        })
        
        # Personalizar labels
        self.fields['old_password'].label = 'Senha Atual'
        self.fields['new_password1'].label = 'Nova Senha'
        self.fields['new_password2'].label = 'Confirmar Nova Senha'


class ContatoWhatsAppForm(forms.ModelForm):
    """Formulário para configurar informações de contato e WhatsApp"""
    
    class Meta:
        model = Restaurante
        fields = ['telefone', 'whatsapp', 'email']
        widgets = {
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
                'data-mask': '(00) 00000-0000'
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '5511999999999',
                'help_text': 'Formato: código do país + DDD + número (sem espaços ou símbolos)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contato@seurestaurante.com.br'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar labels e help texts
        self.fields['telefone'].label = 'Telefone Principal'
        self.fields['telefone'].help_text = 'Telefone que aparecerá nas informações de contato'
        
        self.fields['whatsapp'].label = 'WhatsApp Flutuante'
        self.fields['whatsapp'].help_text = 'Número do WhatsApp no formato: 5511999999999 (código do país + DDD + número). Deixe vazio para desabilitar o botão flutuante.'
        
        self.fields['email'].label = 'E-mail de Contato'
        self.fields['email'].help_text = 'E-mail principal para contato com clientes'
        
        # Tornar todos os campos opcionais
        for field in self.fields.values():
            field.required = False
    
    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp:
            # Remove todos os caracteres não numéricos
            whatsapp = ''.join(filter(str.isdigit, whatsapp))
            
            # Validar formato
            if len(whatsapp) < 10:
                raise forms.ValidationError('Número do WhatsApp deve ter pelo menos 10 dígitos.')
            
            if len(whatsapp) > 15:
                raise forms.ValidationError('Número do WhatsApp não pode ter mais de 15 dígitos.')
            
            # Se não começar com código do país, adicionar 55 (Brasil)
            if not whatsapp.startswith('55') and len(whatsapp) == 11:
                whatsapp = '55' + whatsapp
            
            return whatsapp
        
        return whatsapp
    
    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remover formatação e validar
            telefone_clean = ''.join(filter(str.isdigit, telefone))
            if len(telefone_clean) < 10:
                raise forms.ValidationError('Telefone deve ter pelo menos 10 dígitos.')
        return telefone