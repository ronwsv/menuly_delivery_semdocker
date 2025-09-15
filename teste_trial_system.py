#!/usr/bin/env python
"""
Script de teste para verificar o sistema de trials do Menuly
"""
import os
import sys
import django
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menuly.settings')
django.setup()

from django.utils import timezone
from core.models import Usuario, Restaurante, Plano
from django.contrib.auth.hashers import make_password

def criar_usuario_teste():
    """Cria um usuário de teste para trials"""
    print("🔧 Criando usuário de teste para trials...")
    
    # Verificar se já existe
    try:
        usuario = Usuario.objects.get(username='teste_trial')
        print(f"✅ Usuário de teste já existe: {usuario.username}")
        return usuario
    except Usuario.DoesNotExist:
        pass
    
    # Criar usuário
    usuario = Usuario.objects.create(
        username='teste_trial',
        email='teste@trial.com',
        password=make_password('123456'),
        tipo_usuario='lojista',
        celular='+5511999999999',
        first_name='Teste',
        last_name='Trial',
        is_active=True
    )
    
    # Criar restaurante sem plano (em trial)
    restaurante = Restaurante.objects.create(
        nome='Restaurante Trial',
        descricao='Restaurante de teste para trial',
        telefone='11999999999',
        email='teste@trial.com',
        cep='01310-100',
        logradouro='Av. Paulista',
        numero='1000',
        bairro='Bela Vista',
        cidade='São Paulo',
        estado='SP',
        proprietario=usuario,
        plano=None  # Em trial
    )
    
    print(f"✅ Usuário criado: {usuario.username}")
    print(f"✅ Restaurante criado: {restaurante.nome}")
    return usuario

def criar_usuario_trial_expirado():
    """Cria um usuário com trial expirado"""
    print("⏰ Criando usuário com trial expirado...")
    
    try:
        usuario = Usuario.objects.get(username='teste_trial_expirado')
        print(f"✅ Usuário de teste expirado já existe: {usuario.username}")
        return usuario
    except Usuario.DoesNotExist:
        pass
    
    # Data de 10 dias atrás (trial expirado)
    data_antiga = timezone.now() - timedelta(days=10)
    
    usuario = Usuario.objects.create(
        username='teste_trial_expirado',
        email='expirado@trial.com',
        password=make_password('123456'),
        tipo_usuario='lojista',
        celular='+5511888888888',
        first_name='Trial',
        last_name='Expirado',
        is_active=True
    )
    
    # Alterar data de criação manualmente
    usuario.date_joined = data_antiga
    usuario.save()
    
    # Criar restaurante sem plano
    restaurante = Restaurante.objects.create(
        nome='Restaurante Trial Expirado',
        descricao='Restaurante com trial expirado',
        telefone='11888888888',
        email='expirado@trial.com',
        cep='01310-100',
        logradouro='Av. Paulista',
        numero='2000',
        bairro='Bela Vista',
        cidade='São Paulo',
        estado='SP',
        proprietario=usuario,
        plano=None
    )
    
    print(f"✅ Usuário com trial expirado criado: {usuario.username}")
    print(f"📅 Data de criação: {usuario.date_joined}")
    return usuario

def testar_comando_limpeza():
    """Testa o comando de limpeza de trials"""
    print("\n🧹 Testando comando de limpeza de trials...")
    
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    call_command('desativar_trial_expirados', stdout=out)
    output = out.getvalue()
    
    print(f"📋 Resultado do comando:")
    print(output)

def verificar_status_trials():
    """Verifica o status atual dos trials"""
    print("\n📊 Verificando status dos trials...")
    
    data_limite = timezone.now() - timedelta(days=7)
    
    # Usuários em trial
    trials_ativos = Usuario.objects.filter(
        tipo_usuario='lojista',
        is_active=True,
        restaurantes__plano__isnull=True,
        date_joined__gte=data_limite
    ).distinct()
    
    # Trials expirados
    trials_expirados = Usuario.objects.filter(
        tipo_usuario='lojista',
        is_active=True,
        restaurantes__plano__isnull=True,
        date_joined__lt=data_limite
    ).distinct()
    
    # Contas desativadas
    contas_desativadas = Usuario.objects.filter(
        tipo_usuario='lojista',
        is_active=False,
        restaurantes__plano__isnull=True
    ).distinct()
    
    print(f"✅ Trials ativos: {trials_ativos.count()}")
    print(f"⚠️ Trials expirados: {trials_expirados.count()}")
    print(f"🚫 Contas desativadas: {contas_desativadas.count()}")
    
    print("\n📋 Detalhes dos trials:")
    for usuario in trials_ativos:
        dias = (timezone.now() - usuario.date_joined).days
        print(f"  - {usuario.username}: {dias} dias de trial")
    
    for usuario in trials_expirados:
        dias = (timezone.now() - usuario.date_joined).days
        print(f"  ⚠️ {usuario.username}: {dias} dias (EXPIRADO)")

def main():
    print("🚀 TESTE DO SISTEMA DE TRIALS MENULY")
    print("=" * 50)
    
    # Criar dados de teste
    criar_usuario_teste()
    criar_usuario_trial_expirado()
    
    # Verificar status inicial
    verificar_status_trials()
    
    # Testar comando de limpeza
    testar_comando_limpeza()
    
    # Verificar status após limpeza
    print("\n" + "=" * 50)
    print("📊 STATUS APÓS LIMPEZA:")
    verificar_status_trials()
    
    print("\n✨ Teste concluído!")
    print("💡 Acesse http://127.0.0.1:8600/admin-loja/trials/ para ver a interface")

if __name__ == '__main__':
    main()
