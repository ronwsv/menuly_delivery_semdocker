from django import forms
from core.models import Usuario, Entregador


class CadastroEntregadorForm(forms.ModelForm):
    """Formulário para cadastro de entregador (usuário + entregador)"""
    # Campos do usuário
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        }),
        help_text='Este será seu login no sistema'
    )
    first_name = forms.CharField(
        label='Nome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome'
        })
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu sobrenome'
        })
    )
    celular = forms.CharField(
        label='Celular',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999'
        })
    )
    
    # Campos do entregador
    telefone = forms.CharField(
        label='Telefone para contato',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999'
        }),
        help_text='Telefone que será usado para contato durante as entregas'
    )
    cnh = forms.CharField(
        label='CNH (opcional)',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número da CNH'
        })
    )
    veiculo = forms.CharField(
        label='Veículo',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Moto Honda CG 160'
        })
    )
    dados_bancarios = forms.CharField(
        label='Dados bancários (opcional)',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Banco, agência, conta'
        }),
        help_text='Para recebimento dos pagamentos'
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'celular')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome de usuário'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['username'].required = False  # Não obrigatório pois será preenchido automaticamente
        
        # Definir email como username automaticamente
        self.fields['username'].widget = forms.HiddenInput()
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email
    
    def clean_celular(self):
        celular = self.cleaned_data.get('celular')
        
        # Limpar formatação do celular e padronizar para formato brasileiro
        if celular:
            # Remover caracteres não numéricos
            celular_limpo = ''.join(filter(str.isdigit, celular))
            
            # Validar se tem pelo menos 10 dígitos (formato brasileiro)
            if len(celular_limpo) < 10:
                raise forms.ValidationError('Celular deve ter pelo menos 10 dígitos.')
            
            # Padronizar para formato internacional brasileiro
            if len(celular_limpo) == 10 or len(celular_limpo) == 11:
                # Formato nacional brasileiro - adicionar +55
                celular = '+55' + celular_limpo
            elif not celular_limpo.startswith('55') and len(celular_limpo) > 11:
                # Já pode ter código do país
                celular = '+' + celular_limpo
            else:
                celular = '+55' + celular_limpo
        
        if Usuario.objects.filter(celular=celular).exists():
            raise forms.ValidationError('Este celular já está cadastrado.')
        
        return celular
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = self.data.get('password1')
        password2 = self.data.get('password2')
        email = cleaned_data.get('email')
        
        # Definir email como username automaticamente
        if email:
            cleaned_data['username'] = email
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('As senhas não coincidem.')
            if len(password1) < 8:
                raise forms.ValidationError('A senha deve ter pelo menos 8 caracteres.')
        
        return cleaned_data
    
    def save(self, commit=True):
        # Definir email como username
        email = self.cleaned_data.get('email')
        password = self.data.get('password1')
        
        # Criar usuário manualmente
        user = Usuario(
            username=email,
            email=email,
            first_name=self.cleaned_data.get('first_name'),
            last_name=self.cleaned_data.get('last_name'),
            celular=self.cleaned_data.get('celular'),
            tipo_usuario='entregador'
        )
        
        # Definir senha
        user.set_password(password)
        
        if commit:
            user.save()
            
            # Criar perfil de entregador
            nome_completo = f"{user.first_name} {user.last_name}".strip()
            Entregador.objects.create(
                usuario=user,
                nome=nome_completo,
                telefone=self.cleaned_data.get('telefone', ''),
                cnh=self.cleaned_data.get('cnh', ''),
                veiculo=self.cleaned_data.get('veiculo', ''),
                dados_bancarios=self.cleaned_data.get('dados_bancarios', ''),
            )
        
        return user