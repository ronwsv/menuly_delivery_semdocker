# 🐳 Menuly Delivery - Docker Setup

Este guia mostra como executar o projeto Menuly Delivery usando Docker.

## 📋 Pré-requisitos

- Docker Desktop instalado
- Docker Compose disponível
- 4GB de RAM livre
- 2GB de espaço em disco

## 🚀 Início Rápido

### Desenvolvimento

```bash
# 1. Clone o repositório (se ainda não fez)
git clone <repository-url>
cd projetoMenuly

# 2. Copie o arquivo de ambiente
cp .env.example .env

# 3. Execute o ambiente de desenvolvimento
docker-compose -f docker-compose.dev.yml up --build
```

### Produção

```bash
# 1. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# 2. Execute o ambiente completo
docker-compose up --build -d
```

## 📦 Serviços Inclusos

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| **web** | 8000 | Aplicação Django |
| **db** | 3306 | MySQL 8.0 |
| **redis** | 6379 | Cache e Celery broker |
| **celery** | - | Worker para tarefas assíncronas |
| **celery-beat** | - | Agendador de tarefas |
| **nginx** | 80/443 | Proxy reverso (apenas produção) |

## 🌐 URLs de Acesso

- **Aplicação Principal**: http://localhost:8000
- **Painel Administrativo**: http://localhost:8000/admin/
- **Painel do Lojista**: http://localhost:8000/admin-loja/login/
- **Painel do Entregador**: http://localhost:8000/entregador/login/

## 🔑 Credenciais Padrão

### Superusuário (Django Admin)
- **Usuário**: admin
- **Senha**: admin123

### Lojista de Teste
- **Usuário**: lojista_teste
- **Senha**: senha123

### Entregador de Teste
- **Usuário**: entregador_teste
- **Senha**: senha123

## 📁 Estrutura dos Volumes

```
volumes:
  mysql_data/          # Dados do MySQL
  redis_data/          # Dados do Redis
  staticfiles/         # Arquivos estáticos do Django
  media/              # Uploads e mídia
```

## 🔧 Comandos Úteis

### Gerenciar Containers

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Ver logs
docker-compose logs -f web

# Rebuild containers
docker-compose up --build
```

### Django Management

```bash
# Executar comandos Django
docker-compose exec web python manage.py <command>

# Criar migrações
docker-compose exec web python manage.py makemigrations

# Aplicar migrações
docker-compose exec web python manage.py migrate

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Acessar shell Django
docker-compose exec web python manage.py shell
```

### Banco de Dados

```bash
# Acessar MySQL
docker-compose exec db mysql -u menuly -p menuly_delivery

# Backup do banco
docker-compose exec db mysqldump -u menuly -p menuly_delivery > backup.sql

# Restaurar backup
docker-compose exec -T db mysql -u menuly -p menuly_delivery < backup.sql
```

## 🐛 Troubleshooting

### Problemas Comuns

**1. Porta já está em uso**
```bash
# Verificar processos usando a porta
netstat -tulpn | grep :8000

# Parar containers conflitantes
docker-compose down
```

**2. Permissões de arquivo**
```bash
# Corrigir permissões
sudo chown -R $USER:$USER .
chmod +x docker-init.sh
```

**3. Erro de memória**
```bash
# Limpar containers não utilizados
docker system prune -a

# Verificar uso de memória
docker stats
```

**4. Erro de conexão com banco**
```bash
# Verificar status dos containers
docker-compose ps

# Ver logs do MySQL
docker-compose logs db
```

### Logs Detalhados

```bash
# Logs de todos os serviços
docker-compose logs

# Logs específicos
docker-compose logs web
docker-compose logs db
docker-compose logs redis
```

## 🔒 Configurações de Produção

### Variáveis de Ambiente Importantes

```env
DEBUG=0
SECRET_KEY=sua-chave-secreta-aqui
ALLOWED_HOSTS=seu-dominio.com
SECURE_SSL_REDIRECT=1
```

### Backup Automático

```bash
# Adicionar ao crontab para backup diário
0 2 * * * docker-compose exec db mysqldump -u menuly -p menuly_delivery > /backup/menuly_$(date +\%Y\%m\%d).sql
```

## 📊 Monitoramento

### Health Checks

```bash
# Verificar saúde dos containers
docker-compose ps

# Teste manual da aplicação
curl http://localhost:8000/health/
```

### Métricas

```bash
# Uso de recursos
docker stats

# Espaço em disco dos volumes
docker system df
```

## 🔄 Atualizações

```bash
# Atualizar código
git pull

# Rebuild e restart
docker-compose down
docker-compose up --build -d

# Aplicar migrações se necessário
docker-compose exec web python manage.py migrate
```

## 📞 Suporte

Para problemas específicos do Docker:

1. Verificar logs: `docker-compose logs`
2. Verificar status: `docker-compose ps`
3. Reiniciar serviços: `docker-compose restart`
4. Rebuild completo: `docker-compose down && docker-compose up --build`

---

**Desenvolvido com ❤️ para o Menuly Delivery**