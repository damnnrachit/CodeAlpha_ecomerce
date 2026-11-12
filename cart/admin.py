from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'item_cost')
    readonly_fields = ('item_cost',)

    def item_cost(self, obj):
        return f"${obj.get_cost():.2f}"
    item_cost.short_description = 'Line Cost'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items_display', 'total_price_display', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]

    def total_items_display(self, obj):
        return obj.get_total_items()
    total_items_display.short_description = 'Total Items'

    def total_price_display(self, obj):
        return f"${obj.get_total_price():.2f}"
    total_price_display.short_description = 'Total Price'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('cart__user__username', 'product__name')
