# 🗄️ Comandos para Gerenciamento do Banco de Dados

Este documento contém todos os comandos e scripts para gerenciar o banco de dados MySQL do projeto Menuly Delivery.

## 🚀 Recriação Completa do Banco

### Método 1: Script Python (Recomendado)

```bash
# Executar script Python diretamente
python recreate_database.py
```

### Método 2: Comando Django

```bash
# Usando comando Django personalizado
python manage.py recreate_database

# Com opções
python manage.py recreate_database --force --no-data
```

### Método 3: Script Batch (Windows)

```cmd
# Duplo clique no arquivo ou executar no CMD
recreate_database.bat
```

### Método 4: Script Shell (Linux/Mac)

```bash
# Tornar executável e executar
chmod +x recreate_database.sh
./recreate_database.sh
```

## 📋 O que os Scripts Fazem

1. **🗑️ Drop Database**: Remove o banco `menuly_delivery` se existir
2. **🆕 Create Database**: Cria um novo banco `menuly_delivery`
3. **🧹 Clean Migrations**: Remove arquivos de migração antigos
4. **🔧 Make Migrations**: Cria novas migrações
5. **⚡ Run Migrations**: Aplica todas as migrações
6. **👤 Create Superuser**: Cria usuário admin/admin123
7. **🎯 Create Test Data**: Cria dados de exemplo
8. **📦 Collect Static**: Coleta arquivos estáticos

## 🔧 Comandos Individuais

### Banco de Dados

```bash
# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Status das migrações
python manage.py showmigrations

# Reverter migração específica
python manage.py migrate core 0001

# SQL das migrações
python manage.py sqlmigrate core 0001
```

### Usuários

```bash
# Criar superusuário interativo
python manage.py createsuperuser

# Criar usuário via script
python create_superuser.py

# Alterar senha de usuário
python manage.py changepassword admin
```

### Dados de Teste

```bash
# Criar dados de teste completos
python manage.py criar_dados_teste

# Criar apenas entregador de teste
python manage.py criar_entregador_teste

# Popular planos iniciais
python manage.py popular_planos_iniciais
```

### Arquivos Estáticos

```bash
# Coletar arquivos estáticos
python manage.py collectstatic

# Coletar forçando sobrescrita
python manage.py collectstatic --clear --noinput
```

## ️ Comandos MySQL Diretos

### Conexão

```bash
# Conectar ao MySQL
mysql -h localhost -P 3306 -u root -p

# Conectar ao banco específico
mysql -h localhost -P 3306 -u root -p menuly_delivery
```

### Operações de Banco

```sql
-- Listar bancos
SHOW DATABASES;

-- Usar banco
USE menuly_delivery;

-- Listar tabelas
SHOW TABLES;

-- Descrever tabela
DESCRIBE core_usuario;

-- Ver dados de uma tabela
SELECT * FROM core_usuario LIMIT 5;

-- Contar registros
SELECT COUNT(*) FROM core_pedido;

-- Dropar banco (CUIDADO!)
DROP DATABASE menuly_delivery;

-- Criar banco
CREATE DATABASE menuly_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 🔍 Verificação e Debug

### Verificar Status

```bash
# Verificar conexão com banco
python check_db_simple.py

# Status dos serviços Django
python manage.py check

# Verificar configurações
python manage.py diffsettings
```

### Logs e Debug

```bash
# Shell Django interativo
python manage.py shell

# Shell do banco
python manage.py dbshell

# Executar SQL customizado
python manage.py dbshell < script.sql
```

### Informações do Sistema

```bash
# Versão do Django
python manage.py version

# Apps instalados
python manage.py showmigrations

# Configurações atuais
python -c "from django.conf import settings; print(settings.DATABASES)"
```

## 📊 Monitoramento

### Performance

```sql
-- Tabelas com mais registros
SELECT 
    TABLE_NAME,
    TABLE_ROWS
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'menuly_delivery' 
ORDER BY TABLE_ROWS DESC;

-- Tamanho das tabelas
SELECT 
    TABLE_NAME,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'DB Size in MB'
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'menuly_delivery'
ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC;
```

### Índices

```sql
-- Ver índices de uma tabela
SHOW INDEX FROM core_pedido;

-- Analisar queries lentas
SHOW PROCESSLIST;
```

## 🚨 Troubleshooting

### Problemas Comuns

**1. Erro de conexão MySQL**
```bash
# Verificar se MySQL está rodando
systemctl status mysql  # Linux
brew services list | grep mysql  # Mac
```

**2. Erro de permissão**
```sql
-- Criar usuário MySQL
CREATE USER 'menuly'@'localhost' IDENTIFIED BY 'menuly123';
GRANT ALL PRIVILEGES ON menuly_delivery.* TO 'menuly'@'localhost';
FLUSH PRIVILEGES;
```

**3. Erro de encoding**
```sql
-- Alterar charset do banco
ALTER DATABASE menuly_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**4. Migrações conflitantes**
```bash
# Fake migration (use com cuidado)
python manage.py migrate --fake

# Reverter todas as migrações de um app
python manage.py migrate core zero
```

## 📝 Scripts de Exemplo

### Reset Completo via SQL

```sql
-- Script SQL para reset manual
DROP DATABASE IF EXISTS menuly_delivery;
CREATE DATABASE menuly_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE menuly_delivery;
```

### Backup Automático

```bash
#!/bin/bash
# Script de backup diário
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -p admin menuly_delivery > "backup_menuly_${DATE}.sql"
echo "Backup criado: backup_menuly_${DATE}.sql"
```

---

## 🔗 Links Úteis

- [Django Database API](https://docs.djangoproject.com/en/5.0/topics/db/)
- [Django Migrations](https://docs.djangoproject.com/en/5.0/topics/migrations/)
- [MySQL Documentation](https://dev.mysql.com/doc/)

---

**⚡ Dica**: Sempre faça backup antes de executar comandos destrutivos!