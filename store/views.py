from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Category, Product


def product_list(request):
    """
    Displays the catalog grid with search, category filtering, and 8-per-page pagination.
    """
    category_slug = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.all().order_by('name')
    current_category = None

    # Filter by category if specified
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=current_category)

    # Search by name or description
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Pagination: exactly 8 items per page as required
    paginator = Paginator(products, 8)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    return render(request, 'store/product_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': current_category,
        'search_query': search_query,
        'total_count': paginator.count,
    })


def product_detail(request, slug):
    """
    Displays product details including stock status, description, and related products.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })
