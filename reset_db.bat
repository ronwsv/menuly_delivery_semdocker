@echo off
echo Recriando banco de dados menuly_delivery...
mysql -u root -p -e "source reset_db.sql"
echo.
echo Banco recriado! Execute agora:
echo   python manage.py migrate
echo   python create_superuser.py
pause