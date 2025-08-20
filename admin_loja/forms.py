from django import forms
from core.models import Restaurante
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
