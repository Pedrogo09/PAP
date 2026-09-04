import os
import sys
import django
from pathlib import Path

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bar_escola.settings')
django.setup()

from axes.models import AccessAttempt
AccessAttempt.objects.all().delete()
print("Axes reset successful")
