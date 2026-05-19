from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import StockMovement, Product

@receiver(post_save, sender=StockMovement)
def check_stock_level(sender, instance, created, **kwargs):
    """
    Sinal que verifica o nível de stock após cada movimento.
    Se o stock for inferior ou igual ao min_stock, envia um alerta.
    """
    if created and instance.movement_type == 'out':
        product = instance.product
        if product.stock <= product.min_stock:
            subject = f'⚠️ Alerta de Stock Crítico: {product.name}'
            message = (
                f'O produto "{product.name}" atingiu o nível de stock crítico.\n\n'
                f'Stock Atual: {product.stock}\n'
                f'Stock Mínimo Definido: {product.min_stock}\n\n'
                f'Por favor, providencie a reposição assim que possível.'
            )
            recipient_list = [admin[1] for admin in settings.ADMINS] if settings.ADMINS else []
            
            # Se não houver ADMINS definidos, tentamos enviar para o EMAIL_HOST_USER
            if not recipient_list and settings.EMAIL_HOST_USER:
                recipient_list = [settings.EMAIL_HOST_USER]
                
            if recipient_list:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=True,
                )
