import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from store.models import Product
from .models import Cart, CartItem


def _is_ajax(request):
    """Checks whether the incoming request was made via JavaScript fetch/XHR."""
    return (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.content_type == 'application/json'
    )


@login_required
def cart_detail(request):
    """
    Renders the shopping cart page with all line items, subtotals, and checkout CTA.
    """
    cart, _ = Cart.objects.prefetch_related('items__product').get_or_create(user=request.user)
    items = cart.items.select_related('product').all()

    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'items': items,
    })


@login_required
def add_to_cart(request, product_id):
    """
    Adds a product to the user's cart or increments quantity if already present.
    Supports both traditional POST forms (fallback) and async fetch/AJAX.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Method not allowed. Use POST.")

    product = get_object_or_404(Product, id=product_id, is_active=True)

    # Parse requested quantity
    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
            requested_qty = int(payload.get('quantity', 1))
        else:
            requested_qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError, json.JSONDecodeError):
        requested_qty = 1

    if requested_qty < 1:
        requested_qty = 1

    if product.stock <= 0:
        msg = f"Sorry, '{product.name}' is out of stock."
        if _is_ajax(request):
            return JsonResponse({'success': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect('store:product_detail', slug=product.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 0}
    )

    new_quantity = cart_item.quantity + requested_qty

    if new_quantity > product.stock:
        # Cap at available stock
        actual_added = product.stock - cart_item.quantity
        if actual_added <= 0:
            msg = f"Cannot add more '{product.name}'. You already have the maximum available stock ({product.stock}) in your cart."
            if _is_ajax(request):
                return JsonResponse({'success': False, 'error': msg}, status=400)
            messages.warning(request, msg)
            return redirect('cart:cart_detail')

        cart_item.quantity = product.stock
        cart_item.save()
        msg = f"Only {actual_added} more '{product.name}' was added (maximum available in stock)."
    else:
        cart_item.quantity = new_quantity
        cart_item.save()
        msg = f"Added {requested_qty}x '{product.name}' to your cart."

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_item_count': cart.get_total_items(),
            'cart_total_price': f"{cart.get_total_price():.2f}",
        })

    messages.success(request, msg)
    return redirect('cart:cart_detail')


@login_required
def update_cart_item(request, item_id):
    """
    Updates the quantity of an item in the cart.
    Supports actions: 'increase', 'decrease', or a direct 'quantity' assignment.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Method not allowed. Use POST.")

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    product = cart_item.product

    action = request.POST.get('action')
    direct_qty = request.POST.get('quantity')

    # Parse JSON payload if sent via fetch
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode('utf-8'))
            action = payload.get('action', action)
            direct_qty = payload.get('quantity', direct_qty)
        except json.JSONDecodeError:
            pass

    removed = False

    if action == 'increase':
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            msg = f"Maximum stock for '{product.name}' reached ({product.stock})."
            if _is_ajax(request):
                return JsonResponse({
                    'success': False,
                    'error': msg,
                    'quantity': cart_item.quantity,
                    'item_total': f"{cart_item.get_cost():.2f}",
                    'cart_total': f"{cart.get_total_price():.2f}",
                    'cart_item_count': cart.get_total_items(),
                }, status=400)
            messages.warning(request, msg)
            return redirect('cart:cart_detail')

    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            removed = True

    elif direct_qty is not None:
        try:
            qty = int(direct_qty)
            if qty <= 0:
                cart_item.delete()
                removed = True
            elif qty > product.stock:
                cart_item.quantity = product.stock
                cart_item.save()
                messages.warning(request, f"Adjusted to available stock ({product.stock}).")
            else:
                cart_item.quantity = qty
                cart_item.save()
        except (ValueError, TypeError):
            pass

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'removed': removed,
            'item_id': item_id,
            'quantity': 0 if removed else cart_item.quantity,
            'item_total': "0.00" if removed else f"{cart_item.get_cost():.2f}",
            'cart_total': f"{cart.get_total_price():.2f}",
            'cart_item_count': cart.get_total_items(),
        })

    return redirect('cart:cart_detail')


@login_required
def remove_cart_item(request, item_id):
    """
    Removes an item completely from the cart.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest("Method not allowed. Use POST.")

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    product_name = cart_item.product.name
    cart_item.delete()

    if _is_ajax(request):
        return JsonResponse({
            'success': True,
            'removed': True,
            'item_id': item_id,
            'message': f"Removed '{product_name}' from cart.",
            'cart_total': f"{cart.get_total_price():.2f}",
            'cart_item_count': cart.get_total_items(),
        })

    messages.info(request, f"Removed '{product_name}' from your cart.")
    return redirect('cart:cart_detail')
