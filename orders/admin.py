from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'product_name', 'price_at_purchase', 'quantity', 'item_cost')
    readonly_fields = ('product_name', 'price_at_purchase', 'quantity', 'item_cost')

    def item_cost(self, obj):
        return f"${obj.get_cost():.2f}"
    item_cost.short_description = 'Line Cost'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'full_name',
        'user',
        'total_display',
        'status',
        'total_items',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    search_fields = ('id', 'full_name', 'user__username', 'address', 'city', 'postal_code')
    readonly_fields = ('created_at', 'updated_at', 'total', 'user')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)

    def total_display(self, obj):
        return f"${obj.total:.2f}"
    total_display.short_description = 'Order Total'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'price_at_purchase', 'quantity', 'order_status')
    search_fields = ('order__id', 'product_name', 'order__user__username')

    def order_status(self, obj):
        return obj.order.status
    order_status.short_description = 'Order Status'
