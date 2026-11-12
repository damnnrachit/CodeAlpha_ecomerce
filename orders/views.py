from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
from cart.models import Cart
from store.models import Product
from .models import Order, OrderItem
from .forms import CheckoutForm


@login_required
def checkout_view(request):
    """
    Renders checkout page and processes order creation within an atomic database transaction.
    Guarantees stock integrity and prevents race conditions using select_for_update().
    """
    cart, _ = Cart.objects.prefetch_related('items__product').get_or_create(user=request.user)
    cart_items = list(cart.items.select_related('product').all())

    if not cart_items:
        messages.warning(request, "Your cart is empty. Add products before checking out.")
        return redirect('store:product_list')

    total_price = cart.get_total_price()

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Re-validate and lock all items in the cart
                    insufficient_stock_errors = []
                    locked_products = {}

                    for item in cart_items:
                        product = Product.objects.select_for_update().get(id=item.product.id)
                        locked_products[item.id] = product

                        if not product.is_active:
                            insufficient_stock_errors.append(
                                f"Product '{product.name}' is no longer available for purchase."
                            )
                        elif product.stock < item.quantity:
                            insufficient_stock_errors.append(
                                f"Insufficient stock for '{product.name}'. "
                                f"Available: {product.stock}, in your cart: {item.quantity}."
                            )

                    # If any item has stock issues, abort the transaction
                    if insufficient_stock_errors:
                        for err in insufficient_stock_errors:
                            messages.error(request, err)
                        return render(request, 'orders/checkout.html', {
                            'form': form,
                            'cart': cart,
                            'cart_items': cart_items,
                            'total_price': total_price,
                        })

                    # 2. Create the Order header
                    order = Order.objects.create(
                        user=request.user,
                        full_name=form.cleaned_data['full_name'],
                        address=form.cleaned_data['address'],
                        city=form.cleaned_data['city'],
                        postal_code=form.cleaned_data['postal_code'],
                        total=total_price,
                        status=Order.StatusChoices.PENDING,
                    )

                    # 3. Create OrderItems and decrement stock
                    for item in cart_items:
                        product = locked_products[item.id]
                        product.stock -= item.quantity
                        product.save(update_fields=['stock'])

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            price_at_purchase=product.price,
                            quantity=item.quantity,
                        )

                    # 4. Clear customer shopping cart
                    cart.clear()

                messages.success(
                    request,
                    f"Order #{order.id} placed successfully! Please complete demo payment below."
                )
                return redirect('orders:order_confirmation', order_id=order.id)

            except Exception as exc:
                messages.error(
                    request,
                    f"An error occurred while placing your order: {str(exc)}. Please try again."
                )
        else:
            messages.error(request, "Please correct the shipping address errors below.")
    else:
        # Prepopulate name from user profile if available
        initial_data = {}
        if request.user.get_full_name():
            initial_data['full_name'] = request.user.get_full_name()
        form = CheckoutForm(initial=initial_data)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    })


@login_required
def simulate_payment_view(request, order_id):
    """
    Simulates instantaneous payment for viva/interview demo.
    Transitions order status from Pending to Paid.
    """
    if request.method != 'POST':
        messages.warning(request, "Invalid payment request method.")
        return redirect('orders:order_confirmation', order_id=order_id)

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == Order.StatusChoices.PENDING:
        order.status = Order.StatusChoices.PAID
        order.save(update_fields=['status', 'updated_at'])
        messages.success(
            request,
            f"Payment of ${order.total:.2f} confirmed! Order #{order.id} is now marked as Paid."
        )
    elif order.status == Order.StatusChoices.PAID:
        messages.info(request, f"Order #{order.id} has already been paid for.")
    else:
        messages.warning(request, f"Cannot process payment for order with status '{order.status}'.")

    return redirect('orders:order_confirmation', order_id=order.id)


@login_required
def order_confirmation_view(request, order_id):
    """
    Displays the post-checkout confirmation receipt with simulated payment CTA.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user
    )

    return render(request, 'orders/order_confirmation.html', {
        'order': order,
    })


@login_required
def order_history_view(request):
    """
    Lists all past orders placed by the currently logged-in user.
    Strictly isolated to request.user.
    """
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items')
        .order_by('-created_at')
    )

    return render(request, 'orders/order_history.html', {
        'orders': orders,
    })


@login_required
def order_detail_view(request, order_id):
    """
    Renders detailed breakdown for a single specific order.
    Strictly isolated to request.user.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        user=request.user
    )

    return render(request, 'orders/order_detail.html', {
        'order': order,
    })
