from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from decimal import Decimal
from .models import (
    User, Category, Product, Order, OrderItem,
    Transaction, StockMovement, BarSchedule,
    WeekdayAvailability, SchoolAccount, SchoolTransaction
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'balance', 'is_active']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_per_page = 20
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informação Adicional', {
            'fields': ('user_type', 'phone', 'photo', 'balance')
        }),
    )




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_available', 'needs_restock']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']
    list_per_page = 20
    autocomplete_fields = ['category']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_method', 'total_amount', 'scheduled_date', 'scheduled_time', 'is_priority']
    list_filter = ['status', 'payment_method', 'is_priority', 'scheduled_date']
    search_fields = ['order_number', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['order_number', 'total_amount', 'is_priority']
    inlines = [OrderItemInline]
    date_hierarchy = 'scheduled_date'
    list_per_page = 20
    
    fieldsets = (
        ('Informação do Pedido', {
            'fields': ('order_number', 'user', 'status', 'payment_method', 'total_amount', 'is_priority')
        }),
        ('Agendamento', {
            'fields': ('scheduled_date', 'scheduled_time')
        }),
        ('Notas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
    date_hierarchy = 'created_at'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'reason', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reason']
    date_hierarchy = 'created_at'

    def save_model(self, request, obj, form, change):
        # Se for uma edição (change=True), detetar mudanças na quantidade para movimento 'in'
        if change and obj.movement_type == 'in':
            try:
                old_obj = StockMovement.objects.get(pk=obj.pk)
                old_qty = old_obj.quantity
                new_qty = obj.quantity
                qty_diff = new_qty - old_qty

                # Se quantidade aumentou, descontar custo da escola
                if qty_diff > 0:
                    cost_per_unit = obj.product.price * Decimal('0.50')
                    total_cost = (cost_per_unit * Decimal(qty_diff)).quantize(Decimal('0.01'))

                    sa, _ = SchoolAccount.objects.get_or_create(pk=1, defaults={'balance': Decimal('0.00')})
                    sa.balance -= total_cost
                    sa.save()

                    SchoolTransaction.objects.create(
                        school_account=sa,
                        movement_type='expense',
                        amount=total_cost,
                        description=f'Ajuste stock: {obj.product.name} x{qty_diff} (Admin)',
                        created_by=request.user
                    )
                    # Marcar objeto para não duplicar dedução no save() do modelo
                    obj._admin_processed = True
            except Exception:
                pass  # Não falhar se houver erro

        # Atribuir created_by ao utilizador logado se for criação
        if not change:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)


@admin.register(BarSchedule)
class BarScheduleAdmin(admin.ModelAdmin):
    list_display = ['__str__']
    ordering = ['start_day']
    
    fieldsets = (
        ('Intervalo de Dias', {
            'fields': ('start_day', 'end_day'),
            'description': 'Defina o intervalo de dias da semana em que o bar funciona.'
        }),
        ('Horários', {
            'fields': ('opening_time', 'closing_time'),
            'classes': ('wide',),
            'description': 'Defina o horário de abertura e encerramento para este período.'
        }),
    )


@admin.register(WeekdayAvailability)
class WeekdayAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['weekday', 'start_time', 'end_time', 'is_active']
    list_filter = ['weekday', 'is_active']
    ordering = ['weekday', 'start_time']
    search_fields = []


@admin.register(SchoolAccount)
class SchoolAccountAdmin(admin.ModelAdmin):
    list_display = ['balance', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(SchoolTransaction)
class SchoolTransactionAdmin(admin.ModelAdmin):
    list_display = ['movement_type', 'amount', 'description', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['description']
    
    from django.db import models
    from django.forms import Textarea
    formfield_overrides = {
        models.CharField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }