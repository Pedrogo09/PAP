"""
Comando de gestão para desbloquear utilizadores bloqueados pelo django-axes
Útil para testes da PAP
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from axes.models import AccessAttempt

User = get_user_model()


class Command(BaseCommand):
    help = 'Desbloqueia um utilizador bloqueado pelo django-axes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username do utilizador a desbloquear',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Desbloqueia todos os utilizadores',
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Endereço IP a desbloquear',
        )

    def handle(self, *args, **options):
        if options['all']:
            # Desbloquear todos os utilizadores
            self.stdout.write(self.style.WARNING('A desbloquear TODOS os utilizadores...'))
            count = AccessAttempt.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ {count} registos de bloqueio eliminados! Todos os utilizadores desbloqueados!'))
            return

        if options['username']:
            username = options['username']
            try:
                user = User.objects.get(username=username)
                # Eliminar tentativas de acesso para este utilizador
                count = AccessAttempt.objects.filter(username=username).delete()[0]
                self.stdout.write(self.style.SUCCESS(f'✓ {count} registos de bloqueio eliminados para "{username}"!'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Utilizador "{username}" não encontrado!'))
            return

        if options['ip']:
            ip = options['ip']
            # Eliminar tentativas de acesso para este IP
            count = AccessAttempt.objects.filter(ip_address=ip).delete()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ {count} registros de bloqueio eliminados para IP "{ip}"!'))
            return

        # Se não for especificado nenhum argumento, mostrar instruções
        self.stdout.write(self.style.WARNING('Por favor, especifique um argumento:'))
        self.stdout.write('  --username <username>  : Desbloquear utilizador específico')
        self.stdout.write('  --ip <ip>              : Desbloquear IP específico')
        self.stdout.write('  --all                 : Desbloquear todos os utilizadores')
        self.stdout.write('')
        self.stdout.write('Exemplos:')
        self.stdout.write('  python manage.py unlock_user --username admin')
        self.stdout.write('  python manage.py unlock_user --ip 127.0.0.1')
        self.stdout.write('  python manage.py unlock_user --all')
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Nota: Execute este comando num terminal separado do servidor.'))
