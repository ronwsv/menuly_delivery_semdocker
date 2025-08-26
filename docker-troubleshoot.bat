@echo off
echo ================================================
echo    MENULY DELIVERY - DOCKER TROUBLESHOOT
echo ================================================
echo.

echo Verificando portas ocupadas...
echo.
echo Porta 3306 (MySQL local):
netstat -an | findstr :3306

echo.
echo Porta 3307 (MySQL Docker):
netstat -an | findstr :3307

echo.
echo Porta 6379 (Redis):
netstat -an | findstr :6379

echo.
echo Porta 8000 (Django):
netstat -an | findstr :8000

echo.
echo ================================================
echo COMANDOS PARA RESOLVER CONFLITOS:
echo ================================================
echo.

echo 1. Parar containers existentes:
echo    docker-compose down
echo.

echo 2. Parar MySQL local (se rodando):
echo    net stop mysql80
echo    # ou
echo    net stop mysql
echo.

echo 3. Verificar containers rodando:
echo    docker ps
echo.

echo 4. Limpar containers parados:
echo    docker container prune
echo.

echo 5. Remover volumes (CUIDADO - apaga dados!):
echo    docker-compose down -v
echo.

echo 6. Rebuild completo:
echo    docker-compose down -v
echo    docker-compose up --build
echo.

echo ================================================
echo COMANDOS DE TESTE:
echo ================================================
echo.

echo Testar MySQL Docker (porta 3307):
echo    mysql -h 127.0.0.1 -P 3307 -u menuly -p
echo.

echo Testar aplicacao:
echo    curl http://localhost:8000
echo.

echo Ver logs dos containers:
echo    docker-compose logs
echo    docker-compose logs web
echo    docker-compose logs db
echo.

pause