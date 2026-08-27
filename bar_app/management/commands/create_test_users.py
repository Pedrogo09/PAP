from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Cria utilizadores de teste para demonstração'

    def handle(self, *args, **options):
        test_users = [
            {
                'username': 'PROFESSOR',
                'password': 'PROFESSOR',
                'user_type': 'teacher',
                'email': 'professor@demo.local',
                'first_name': 'Professor',
                'last_name': 'Teste'
            },
            {
                'username': 'ALUNO',
                'password': 'ALUNO',
                'user_type': 'student',
                'email': 'aluno@demo.local',
                'first_name': 'Aluno',
                'last_name': 'Teste'
            },
            {
                'username': 'FUNCIONARIO',
                'password': 'FUNCIONARIO',
                'user_type': 'staff',
                'email': 'funcionario@demo.local',
                'first_name': 'Funcionário',
                'last_name': 'Teste'
            }
        ]

        for user_data in test_users:
            username = user_data['username']
            
            # Verificar se utilizador já existe
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Utilizador {username} já existe. A saltar...')
                )
                continue
            
            # Criar utilizador
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                user_type=user_data['user_type'],
                email_verified=True  # Auto-verificar para testes
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Utilizador {username} criado com sucesso!')
            )
            self.stdout.write(f'  - Tipo: {user.get_user_type_display()}')
            self.stdout.write(f'  - Password: {user_data["password"]}')
        
        self.stdout.write(
            self.style.SUCCESS('\nUtilizadores de teste criados com sucesso!')
        )
