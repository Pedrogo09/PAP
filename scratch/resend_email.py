import os
import sys
import django
from pathlib import Path

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Carregar variáveis de ambiente do .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bar_escola.settings')
django.setup()

from django.core.mail import EmailMessage
from bar_app.models import User
from bar_app.utils import make_verification_token

def resend_email(email):
    try:
        user = User.objects.get(email=email)
        token = make_verification_token(user)
        # Usamos localhost para o link no terminal, mas o email real usaria o domínio
        verify_url = f"http://localhost:8000/verify_email/{token}/"
        
        subject = 'Confirme o seu email - Bar Escolar'
        body = (
            f'Olá {user.username},\nclique no link abaixo para activar a sua conta:\n'
            f'{verify_url}\n\nSe não pediu este email, pode ignorá-lo.'
        )
        
        email_message = EmailMessage(subject, body, to=[user.email])
        email_message.send(fail_silently=False)
        print(f"E-mail enviado com sucesso para {email}")
    except User.DoesNotExist:
        print(f"Erro: Utilizador com e-mail {email} não encontrado.")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")

if __name__ == "__main__":
    resend_email("boas45811@gmail.com")
