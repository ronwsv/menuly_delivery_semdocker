# 🚨 Docker Port Conflict - Solução Rápida

## Problema
```
Error: ports are not available: exposing port TCP 0.0.0.0:3306
```

A porta 3306 já está sendo usada pelo MySQL local.

## ✅ Solução (já implementada)

Os arquivos `docker-compose.yml` e `docker-compose.dev.yml` já foram alterados para usar a **porta 3307**.

## 🔧 Comandos para Resolver

### 1. Parar containers existentes
```bash
docker-compose down
```

### 2. Limpar containers antigos
```bash
docker container prune -f
docker system prune -f
```

### 3. Subir com a nova configuração
```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml up --build

# Ou produção
docker-compose up --build
```

## 🌐 Novas Portas de Acesso

| Serviço | Porta Local | Porta Container |
|---------|-------------|-----------------|
| **MySQL** | **3307** | 3306 |
| **Redis** | 6379 | 6379 |
| **Django** | 8000 | 8000 |
| **Nginx** | 80 | 80 |

## 🔍 Verificar Portas Ocupadas

```bash
# Windows
netstat -an | findstr :3306
netstat -an | findstr :3307

# Linux/Mac  
lsof -i :3306
lsof -i :3307
```

## 🗄️ Conectar ao MySQL Docker

```bash
# Nova conexão (porta 3307)
mysql -h 127.0.0.1 -P 3307 -u menuly -p

# Senha: menuly123
```

## 📱 URLs da Aplicação (inalteradas)

- **App**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/
- **Lojista**: http://localhost:8000/admin-loja/login/

## 🛠️ Troubleshooting

### Container não sobe
```bash
# Ver logs detalhados
docker-compose logs db
docker-compose logs web
```

### Reset completo
```bash
# CUIDADO: Apaga todos os dados!
docker-compose down -v
docker system prune -a -f
docker-compose up --build
```

### MySQL local conflitando
```bash
# Windows - Parar MySQL local
net stop mysql80
# ou
net stop mysql

# Linux/Mac - Parar MySQL local
sudo service mysql stop
# ou
brew services stop mysql
```

## ✅ Teste Final

```bash
# 1. Subir containers
docker-compose -f docker-compose.dev.yml up -d

# 2. Verificar se estão rodando
docker-compose ps

# 3. Testar aplicação
curl http://localhost:8000
```

---

**🎯 Resumo**: A porta foi alterada de 3306 para 3307 nos arquivos Docker. Apenas execute `docker-compose down` e suba novamente com `docker-compose up --build`!