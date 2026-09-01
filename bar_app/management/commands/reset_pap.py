"""
Comando Django para reset da base de dados para testes/apresentação da PAP
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import shutil
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Reset da base de dados para testes/apresentação da PAP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Executar sem confirmação',
        )

    def handle(self, *args, **options):
        # Confirmação
        if not options['yes']:
            self.stdout.write(self.style.WARNING('ESTA OPERAÇÃO APAGARÁ OS DADOS DE TESTE DA BASE DE DADOS.'))
            response = input('Continuar? [y/N]: ')
            if response.lower() != 'y':
                self.stdout.write(self.style.ERROR('Operação cancelada.'))
                return

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.NOTICE('INICIANDO RESET DA PAP'))
        self.stdout.write('='*60 + '\n')

        # Contadores para estatísticas
        stats = {
            'admins_kept': 0,
            'students_removed': 0,
            'teachers_removed': 0,
            'staff_removed': 0,
            'orders_removed': 0,
            'transactions_removed': 0,
            'reviews_removed': 0,
            'favorites_removed': 0,
            'stock_movements_removed': 0,
            'school_transactions_removed': 0,
            'products_kept': 0,
            'categories_kept': 0,
        }

        try:
            # Backup automático
            self.stdout.write('1. Criando backup da base de dados...')
            backup_path = self.create_backup()
            self.stdout.write(self.style.SUCCESS(f'   Backup criado: {backup_path}'))

            # Executar reset dentro de transação
            with transaction.atomic():
                # Limpar utilizadores de teste
                self.stdout.write('\n2. Limpando utilizadores de teste...')
                stats.update(self.clean_test_users())

                # Limpar pedidos e dados relacionados
                self.stdout.write('\n3. Limpando pedidos e dados relacionados...')
                stats.update(self.clean_orders())

                # Limpar dados financeiros
                self.stdout.write('\n4. Limpando dados financeiros...')
                stats.update(self.clean_financial_data())

                # Reset de stock
                self.stdout.write('\n5. Resetando stock...')
                stats.update(self.reset_stock())

                # Criar contas de teste
                self.stdout.write('\n6. Criando contas de teste...')
                self.create_test_accounts()

            # Verificações finais
            self.stdout.write('\n7. Executando verificações...')
            self.run_verifications(stats)

            # Resumo final
            self.print_summary(stats)

            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('RESET CONCLUÍDO COM SUCESSO.'))
            self.stdout.write('='*60 + '\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERRO DURANTE O RESET: {str(e)}'))
            raise

    def create_backup(self):
        """Cria backup da base de dados com timestamp"""
        from django.db import connections
        
        db_name = settings.DATABASES['default']['NAME']
        db_path = Path(db_name)
        
        if not db_path.exists():
            self.stdout.write(self.style.WARNING('   Base de dados não encontrada, pulando backup.'))
            return None
        
        # Criar pasta de backups
        backups_dir = Path('backups')
        backups_dir.mkdir(exist_ok=True)
        
        # Nome do backup com timestamp
        timestamp = timezone.now().strftime('%Y-%m-%d_%H%M%S')
        backup_name = f'pap_backup_{timestamp}.sqlite3'
        backup_path = backups_dir / backup_name
        
        # Copiar ficheiro
        shutil.copy2(db_path, backup_path)
        
        return str(backup_path)

    def clean_test_users(self):
        """Remove utilizadores de teste (student, teacher, staff)"""
        from bar_app.models import User, Student, Teacher, Staff
        
        stats = {
            'students_removed': 0,
            'teachers_removed': 0,
            'staff_removed': 0,
            'admins_kept': 0,
        }
        
        # Contar admins antes de limpar
        stats['admins_kept'] = User.objects.filter(user_type='admin').count()
        
        # Apagar utilizadores por tipo (CASCADE apaga profiles relacionados)
        for user_type, stat_key in [('student', 'students_removed'), 
                                     ('teacher', 'teachers_removed'), 
                                     ('staff', 'staff_removed')]:
            count = User.objects.filter(user_type=user_type).count()
            User.objects.filter(user_type=user_type).delete()
            stats[stat_key] = count
        
        return stats

    def clean_orders(self):
        """Limpa pedidos e dados relacionados"""
        from bar_app.models import Order, OrderItem, OrderReview, StockMovement
        
        stats = {
            'orders_removed': 0,
            'reviews_removed': 0,
            'stock_movements_removed': 0,
        }
        
        # Contar antes de apagar
        stats['orders_removed'] = Order.objects.count()
        stats['reviews_removed'] = OrderReview.objects.count()
        stats['stock_movements_removed'] = StockMovement.objects.count()
        
        # Apagar (CASCADE apaga OrderItems, OrderReview)
        Order.objects.all().delete()
        StockMovement.objects.all().delete()
        
        return stats

    def clean_financial_data(self):
        """Limpa dados financeiros de teste"""
        from bar_app.models import Transaction, SchoolTransaction, SchoolAccount
        
        stats = {
            'transactions_removed': 0,
            'school_transactions_removed': 0,
        }
        
        # Contar antes de apagar
        stats['transactions_removed'] = Transaction.objects.count()
        stats['school_transactions_removed'] = SchoolTransaction.objects.count()
        
        # Apagar transações
        Transaction.objects.all().delete()
        SchoolTransaction.objects.all().delete()
        
        # Resetar saldo da escola para valor inicial
        school_account, _ = SchoolAccount.objects.get_or_create(pk=1, defaults={'balance': Decimal('1000.00')})
        school_account.balance = Decimal('1000.00')
        school_account.save()
        
        return stats

    def reset_stock(self):
        """Reset de stock com arredondamento para múltiplos de 5"""
        from bar_app.models import Product
        
        stats = {
            'products_kept': 0,
            'categories_kept': 0,
        }
        
        # Contar produtos e categorias
        stats['products_kept'] = Product.objects.count()
        stats['categories_kept'] = Product.objects.values('category').distinct().count()
        
        # Arredondar stock para múltiplos de 5
        for product in Product.objects.all():
            if product.stock > 0:
                rounded_stock = round(product.stock / 5) * 5
                # Se ficar 0, usar 5 se original era > 2
                if rounded_stock == 0 and product.stock >= 3:
                    rounded_stock = 5
                product.stock = rounded_stock
                product.save()
        
        return stats

    def create_test_accounts(self):
        """Cria as três contas de teste"""
        from bar_app.models import User
        
        test_accounts = [
            {
                'username': 'alunoteste',
                'email': 'alunoteste@gmail.com',
                'password': 'alunoteste123',
                'user_type': 'student',
                'first_name': 'Aluno',
                'last_name': 'Teste',
                'turma': '10PI',
                'escalao': 'A',
                'balance': Decimal('20.00'),
            },
            {
                'username': 'professorteste',
                'email': 'professorteste@gmail.com',
                'password': 'professorteste123',
                'user_type': 'teacher',
                'first_name': 'Professor',
                'last_name': 'Teste',
                'balance': Decimal('50.00'),
            },
            {
                'username': 'funcionarioteste',
                'email': 'funcionarioteste@gmail.com',
                'password': 'funcionarioteste123',
                'user_type': 'staff',
                'first_name': 'Funcionário',
                'last_name': 'Teste',
                'is_staff': True,
                'balance': Decimal('50.00'),
            },
        ]
        
        for account_data in test_accounts:
            username = account_data.pop('username')
            password = account_data.pop('password')
            
            # Verificar se já existe (idempotência)
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'   [SKIP] {username} já existe')
                continue
            
            # Criar utilizador
            user = User.objects.create_user(
                username=username,
                password=password,
                is_active=True,
                email_verified=True,
                **account_data
            )
            
            # Criar profile relacionado se necessário
            if user.user_type == 'student':
                from bar_app.models import Student
                Student.objects.create(
                    user=user,
                    student_number=f'ST{username.upper()}',
                    grade='10',
                    class_name=user.turma
                )
            elif user.user_type == 'teacher':
                from bar_app.models import Teacher
                Teacher.objects.create(
                    user=user,
                    employee_number=f'TC{username.upper()}',
                    department='Geral'
                )
            elif user.user_type == 'staff':
                from bar_app.models import Staff
                Staff.objects.create(
                    user=user,
                    employee_number=f'SF{username.upper()}',
                    position='Funcionário'
                )
            
            self.stdout.write(self.style.SUCCESS(f'   [OK] {username}'))

    def run_verifications(self, stats):
        """Executa verificações automáticas"""
        from bar_app.models import User, Transaction, Product, Order
        
        # Verificar que não há utilizadores de teste antigos
        old_students = User.objects.filter(user_type='student').exclude(username='alunoteste').count()
        old_teachers = User.objects.filter(user_type='teacher').exclude(username='professorteste').count()
        old_staff = User.objects.filter(user_type='staff').exclude(username='funcionarioteste').count()
        
        if old_students == 0:
            self.stdout.write(self.style.SUCCESS('   [OK] Nenhum aluno antigo encontrado'))
        else:
            self.stdout.write(self.style.ERROR(f'   [FAIL] {old_students} alunos antigos encontrados'))
        
        if old_teachers == 0:
            self.stdout.write(self.style.SUCCESS('   [OK] Nenhum professor antigo encontrado'))
        else:
            self.stdout.write(self.style.ERROR(f'   [FAIL] {old_teachers} professores antigos encontrados'))
        
        if old_staff == 0:
            self.stdout.write(self.style.SUCCESS('   [OK] Nenhum funcionário antigo encontrado'))
        else:
            self.stdout.write(self.style.ERROR(f'   [FAIL] {old_staff} funcionários antigos encontrados'))
        
        # Verificar que não há transações antigas
        old_transactions = Transaction.objects.count()
        if old_transactions == 0:
            self.stdout.write(self.style.SUCCESS('   [OK] Nenhuma transação de teste antiga encontrada'))
        else:
            self.stdout.write(self.style.ERROR(f'   [FAIL] {old_transactions} transações antigas encontradas'))
        
        # Verificar que produtos foram preservados
        if stats['products_kept'] > 0:
            self.stdout.write(self.style.SUCCESS(f'   [OK] Produtos preservados ({stats["products_kept"]})'))
        else:
            self.stdout.write(self.style.WARNING('   [WARN] Nenhum produto encontrado'))
        
        # Verificar que admins foram preservados
        if stats['admins_kept'] > 0:
            self.stdout.write(self.style.SUCCESS(f'   [OK] Admins preservados ({stats["admins_kept"]})'))
        else:
            self.stdout.write(self.style.WARNING('   [WARN] Nenhum admin encontrado'))

    def print_summary(self, stats):
        """Imprime resumo das operações"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('RESET DA PAP CONCLUÍDO\n')
        
        self.stdout.write(f'Admins mantidos: {stats["admins_kept"]}')
        self.stdout.write(f'Alunos removidos: {stats["students_removed"]}')
        self.stdout.write(f'Professores removidos: {stats["teachers_removed"]}')
        self.stdout.write(f'Funcionários removidos: {stats["staff_removed"]}')
        self.stdout.write(f'Pedidos removidos: {stats["orders_removed"]}')
        self.stdout.write(f'Transações removidas: {stats["transactions_removed"]}')
        self.stdout.write(f'Reviews removidas: {stats["reviews_removed"]}')
        self.stdout.write(f'Movimentos de stock removidos: {stats["stock_movements_removed"]}')
        self.stdout.write(f'Transações da escola removidas: {stats["school_transactions_removed"]}')
        
        self.stdout.write(f'\nProdutos mantidos: {stats["products_kept"]}')
        self.stdout.write(f'Categorias mantidas: {stats["categories_kept"]}')
        
        self.stdout.write('\nContas de teste criadas:')
        self.stdout.write(self.style.SUCCESS('[OK] alunoteste'))
        self.stdout.write(self.style.SUCCESS('[OK] professorteste'))
        self.stdout.write(self.style.SUCCESS('[OK] funcionarioteste'))
