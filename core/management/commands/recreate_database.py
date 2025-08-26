from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import mysql.connector
from mysql.connector import Error
import os
import sys

class Command(BaseCommand):
    help = 'Recria o banco de dados MySQL do zero'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a recriação sem confirmação',
        )
        parser.add_argument(
            '--no-data',
            action='store_true',
            help='Não cria dados de teste',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.HTTP_INFO('=' * 50)
        )
        self.stdout.write(
            self.style.HTTP_INFO('RECREATE DATABASE - MENULY DELIVERY')
        )
        self.stdout.write(
            self.style.HTTP_INFO('=' * 50)
        )

        # Obter configurações do banco
        db_config = settings.DATABASES['default']
        
        if not options['force']:
            self.stdout.write(
                self.style.WARNING('\n⚠️  ATENÇÃO: Este comando irá DELETAR todos os dados do banco!')
            )
            self.stdout.write(f"\nConfiguração do banco:")
            self.stdout.write(f"  Host: {db_config['HOST']}:{db_config['PORT']}")
            self.stdout.write(f"  Database: {db_config['NAME']}")
            self.stdout.write(f"  User: {db_config['USER']}")
            
            confirm = input('\nDeseja continuar? (s/N): ')
            if confirm.lower() not in ['s', 'sim', 'yes', 'y']:
                self.stdout.write(
                    self.style.ERROR('❌ Operação cancelada pelo usuário.')
                )
                return

        # 1. Recriar banco de dados
        if not self._recreate_database(db_config):
            return

        # 2. Remover migrações antigas
        self._clean_migrations()

        # 3. Criar novas migrações
        self.stdout.write('\n🔧 Criando migrações...')
        call_command('makemigrations', verbosity=0)
        self.stdout.write(self.style.SUCCESS('✅ Migrações criadas!'))

        # 4. Aplicar migrações
        self.stdout.write('\n🔧 Aplicando migrações...')
        call_command('migrate', verbosity=0)
        self.stdout.write(self.style.SUCCESS('✅ Migrações aplicadas!'))

        # 5. Criar superusuário
        self._create_superuser()

        # 6. Criar dados de teste (se solicitado)
        if not options['no_data']:
            self._create_test_data()

        # 7. Coletar arquivos estáticos
        self.stdout.write('\n🔧 Coletando arquivos estáticos...')
        try:
            call_command('collectstatic', interactive=False, verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Arquivos estáticos coletados!'))
        except:
            self.stdout.write(self.style.WARNING('⚠️ Erro ao coletar arquivos estáticos'))

        self._show_final_info()

    def _recreate_database(self, db_config):
        """Recria o banco de dados MySQL"""
        self.stdout.write('\n🗄️ Recriando banco de dados MySQL...')
        
        connection = None
        try:
            # Conectar ao MySQL (sem especificar database)
            connection = mysql.connector.connect(
                host=db_config['HOST'],
                port=int(db_config['PORT']),
                user=db_config['USER'],
                password=db_config['PASSWORD']
            )
            
            cursor = connection.cursor()
            
            # Dropar database se existir
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_config['NAME']}`")
            self.stdout.write(f"🗑️ Database '{db_config['NAME']}' dropado")
            
            # Criar database
            cursor.execute(f"CREATE DATABASE `{db_config['NAME']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.stdout.write(self.style.SUCCESS(f"✅ Database '{db_config['NAME']}' criado com sucesso!"))
            
            return True
            
        except Error as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro ao recriar database: {e}")
            )
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def _clean_migrations(self):
        """Remove arquivos de migração antigos"""
        self.stdout.write('\n🧹 Limpando arquivos de migração...')
        
        migration_dirs = [
            'core/migrations',
            'admin_loja/migrations'
        ]
        
        for migration_dir in migration_dirs:
            if os.path.exists(migration_dir):
                for file in os.listdir(migration_dir):
                    if file.endswith('.py') and file != '__init__.py':
                        file_path = os.path.join(migration_dir, file)
                        os.remove(file_path)
                        self.stdout.write(f"🗑️ Removido: {file_path}")

    def _create_superuser(self):
        """Cria o superusuário"""
        self.stdout.write('\n👤 Criando superusuário...')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@menuly.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS("✅ Superusuário 'admin' criado com sucesso!"))
            else:
                self.stdout.write("ℹ️ Superusuário 'admin' já existe!")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro ao criar superusuário: {e}")
            )

    def _create_test_data(self):
        """Cria dados de teste"""
        self.stdout.write('\n🎯 Criando dados de teste...')
        
        try:
            call_command('criar_dados_teste')
            self.stdout.write(self.style.SUCCESS("✅ Dados de teste criados com sucesso!"))
        except:
            self.stdout.write(self.style.WARNING("⚠️ Erro ao criar dados de teste. Continuando..."))
        
        try:
            call_command('criar_entregador_teste')
            self.stdout.write(self.style.SUCCESS("✅ Entregador de teste criado com sucesso!"))
        except:
            self.stdout.write(self.style.WARNING("⚠️ Erro ao criar entregador de teste. Continuando..."))

    def _show_final_info(self):
        """Mostra informações finais"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS('🎉 DATABASE RECRIADO COM SUCESSO!')
        )
        self.stdout.write('=' * 50)
        
        self.stdout.write('\n📋 INFORMAÇÕES DE ACESSO:')
        self.stdout.write('=' * 30)
        
        self.stdout.write('\n🌐 URLs:')
        self.stdout.write('  • Aplicação: http://localhost:8000')
        self.stdout.write('  • Admin Django: http://localhost:8000/admin/')
        self.stdout.write('  • Painel Lojista: http://localhost:8000/admin-loja/login/')
        self.stdout.write('  • Painel Entregador: http://localhost:8000/entregador/login/')
        
        self.stdout.write('\n🔑 Credenciais:')
        self.stdout.write('  • Superusuário: admin / admin123')
        self.stdout.write('  • Lojista Teste: lojista_teste / senha123')
        self.stdout.write('  • Entregador Teste: entregador_teste / senha123')
        
        db_config = settings.DATABASES['default']
        self.stdout.write('\n🗄️ Banco de Dados:')
        self.stdout.write(f"  • Host: {db_config['HOST']}:{db_config['PORT']}")
        self.stdout.write(f"  • Database: {db_config['NAME']}")
        self.stdout.write(f"  • Usuário: {db_config['USER']}")
        
        self.stdout.write('\n🚀 Para iniciar o servidor:')
        self.stdout.write('  python manage.py runserver')
        
        self.stdout.write('\n' + '=' * 50)