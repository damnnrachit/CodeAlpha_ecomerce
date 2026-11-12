/**
 * SwiftShop - Vanilla JavaScript Cart Interactivity
 * Provides seamless AJAX live cart updates with graceful fallback for non-JS environments.
 */

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------
    // 1. Helper: Get CSRF Token from Cookie or Input
    // -------------------------------------------------------------
    function getCsrfToken() {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) return input.value;

        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                return decodeURIComponent(cookie.substring('csrftoken='.length));
            }
        }
        return '';
    }

    // -------------------------------------------------------------
    // 2. Helper: Show Flash Notification Banner
    // -------------------------------------------------------------
    function showNotification(message, type = 'success') {
        const container = document.querySelector('.container.mt-3');
        if (!container) return;

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show d-flex align-items-center shadow-sm`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            <i class="bi bi-check-circle-fill me-2"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        container.prepend(alertDiv);

        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 250);
        }, 4000);
    }

    // -------------------------------------------------------------
    // 3. Navbar Cart Badge Updater
    // -------------------------------------------------------------
    function updateNavbarCartCount(count) {
        const badge = document.getElementById('navbar-cart-count');
        if (badge) {
            badge.textContent = count;
            // Brief pop animation
            badge.style.transform = 'scale(1.25)';
            setTimeout(() => {
                badge.style.transform = 'scale(1)';
            }, 200);
        }
    }

    // -------------------------------------------------------------
    // 4. Product Detail Page: Quantity Selector Buttons
    // -------------------------------------------------------------
    const qtyInput = document.getElementById('quantity');
    const btnDecrease = document.querySelector('.btn-qty-decrease');
    const btnIncrease = document.querySelector('.btn-qty-increase');

    if (qtyInput && btnDecrease && btnIncrease) {
        const min = parseInt(qtyInput.getAttribute('min') || '1', 10);
        const max = parseInt(qtyInput.getAttribute('max') || '999', 10);

        btnDecrease.addEventListener('click', function () {
            let current = parseInt(qtyInput.value, 10) || 1;
            if (current > min) {
                qtyInput.value = current - 1;
            }
        });

        btnIncrease.addEventListener('click', function () {
            let current = parseInt(qtyInput.value, 10) || 1;
            if (current < max) {
                qtyInput.value = current + 1;
            }
        });
    }

    // -------------------------------------------------------------
    // 5. AJAX "Add to Cart" Handler (Catalog & Detail)
    // -------------------------------------------------------------
    document.querySelectorAll('.ajax-add-to-cart-form').forEach(form => {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalHtml = submitBtn.innerHTML;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Adding...';

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                        'Accept': 'application/json',
                    },
                    body: formData,
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    updateNavbarCartCount(data.cart_item_count);
                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.error || 'Failed to add product to cart.', 'danger');
                }
            } catch (err) {
                // Graceful fallback: submit form normally if network/AJAX fails
                form.submit();
                return;
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }
        });
    });

    // -------------------------------------------------------------
    // 6. Cart Page: Live AJAX Quantity Update
    // -------------------------------------------------------------
    document.querySelectorAll('.cart-qty-form').forEach(form => {
        const decreaseBtn = form.querySelector('.btn-qty-decrease-ajax');
        const increaseBtn = form.querySelector('.btn-qty-increase-ajax');

        async function handleQtyChange(action) {
            const formData = new FormData(form);
            formData.set('action', action);

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                        'Accept': 'application/json',
                    },
                    body: formData,
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    const itemId = data.item_id;
                    const row = document.getElementById(`cart-item-row-${itemId}`);

                    if (data.removed) {
                        if (row) {
                            row.style.transition = 'opacity 0.25s ease';
                            row.style.opacity = '0';
                            setTimeout(() => row.remove(), 250);
                        }
                    } else {
                        const input = document.getElementById(`qty-input-${itemId}`);
                        if (input) input.value = data.quantity;

                        const subtotalSpan = document.getElementById(`item-subtotal-${itemId}`);
                        if (subtotalSpan) subtotalSpan.textContent = data.item_total;
                    }

                    // Update summary panel
                    const summaryTotal = document.getElementById('cart-summary-total');
                    if (summaryTotal) summaryTotal.textContent = data.cart_total;

                    const summarySubtotal = document.getElementById('cart-summary-subtotal');
                    if (summarySubtotal) summarySubtotal.textContent = data.cart_total;

                    const summaryCount = document.getElementById('cart-summary-items-count');
                    if (summaryCount) summaryCount.textContent = data.cart_item_count;

                    updateNavbarCartCount(data.cart_item_count);

                    // Check if cart is now empty
                    if (data.cart_item_count === 0) {
                        const wrapper = document.getElementById('cart-content-wrapper');
                        const emptyPlaceholder = document.getElementById('cart-empty-placeholder');
                        if (wrapper) wrapper.remove();
                        if (emptyPlaceholder) emptyPlaceholder.classList.remove('d-none');
                    }
                } else {
                    showNotification(data.error || 'Could not update quantity.', 'warning');
                }
            } catch (err) {
                // Graceful fallback to regular form submit
                form.submit();
            }
        }

        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', function (e) {
                e.preventDefault();
                handleQtyChange('decrease');
            });
        }

        if (increaseBtn) {
            increaseBtn.addEventListener('click', function (e) {
                e.preventDefault();
                handleQtyChange('increase');
            });
        }
    });

    // -------------------------------------------------------------
    // 7. Cart Page: Live AJAX Remove Item
    // -------------------------------------------------------------
    document.querySelectorAll('.cart-remove-form').forEach(form => {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const itemId = form.querySelector('.btn-remove-ajax').getAttribute('data-item-id');
            const row = document.getElementById(`cart-item-row-${itemId}`);

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': getCsrfToken(),
                        'Accept': 'application/json',
                    },
                    body: formData,
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    if (row) {
                        row.style.transition = 'opacity 0.25s ease';
                        row.style.opacity = '0';
                        setTimeout(() => row.remove(), 250);
                    }

                    const summaryTotal = document.getElementById('cart-summary-total');
                    if (summaryTotal) summaryTotal.textContent = data.cart_total;

                    const summarySubtotal = document.getElementById('cart-summary-subtotal');
                    if (summarySubtotal) summarySubtotal.textContent = data.cart_total;

                    const summaryCount = document.getElementById('cart-summary-items-count');
                    if (summaryCount) summaryCount.textContent = data.cart_item_count;

                    updateNavbarCartCount(data.cart_item_count);
                    showNotification(data.message, 'info');

                    if (data.cart_item_count === 0) {
                        const wrapper = document.getElementById('cart-content-wrapper');
                        const emptyPlaceholder = document.getElementById('cart-empty-placeholder');
                        if (wrapper) wrapper.remove();
                        if (emptyPlaceholder) emptyPlaceholder.classList.remove('d-none');
                    }
                } else {
                    form.submit();
                }
            } catch (err) {
                form.submit();
            }
        });
    });
});
