from .models import Cart


def cart_context(request):
    """
    Exposes cart statistics globally to all templates for navbar badges and headers.
    Safe against non-authenticated requests and uncreated carts.
    """
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.prefetch_related('items').get(user=request.user)
            item_count = sum(item.quantity for item in cart.items.all())
            total_price = cart.get_total_price()
        except Cart.DoesNotExist:
            item_count = 0
            total_price = 0
    else:
        item_count = 0
        total_price = 0

    return {
        'cart_item_count': item_count,
        'cart_total_price': total_price,
    }
