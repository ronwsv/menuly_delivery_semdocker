from django import forms
from django.db import models
from core.models import Restaurante, Categoria, Produto, HorarioFuncionamento
from .models import Impressora


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
            'tempo_preparo', 'calorias', 'ingredientes', 'alergicos', 'ordem'
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
            'alergicos', 'imagem_principal'
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
        
        if preco_promocional and preco_promocional >= preco:
            raise forms.ValidationError(
                'Preço promocional deve ser menor que o preço normal.'
            )
        
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
