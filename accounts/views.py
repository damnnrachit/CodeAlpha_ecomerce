from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from cart.models import Cart
from .forms import CustomUserCreationForm, LoginForm


def register_view(request):
    """
    Handles new user registration.
    Automatically initializes the user's cart and logs them in upon successful signup.
    """
    if request.user.is_authenticated:
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure shopping cart exists for the new user
            Cart.objects.get_or_create(user=user)
            # Log the user in immediately
            login(request, user)
            messages.success(
                request,
                f"Welcome to SwiftShop, {user.username}! Your account has been created."
            )
            return redirect('store:product_list')
        else:
            messages.error(
                request,
                "Registration failed. Please correct the errors below."
            )
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Authenticates existing users with redirect safety for 'next' parameter.
    """
    if request.user.is_authenticated:
        return redirect('store:product_list')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    Cart.objects.get_or_create(user=user)
                    messages.success(request, f"Welcome back, {user.username}!")

                    # Safe redirect check
                    if next_url and url_has_allowed_host_and_scheme(
                        url=next_url,
                        allowed_hosts={request.get_host()}
                    ):
                        return redirect(next_url)
                    return redirect('store:product_list')
                else:
                    messages.error(request, "This account is inactive.")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please enter valid credentials.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    """
    Logs out user and redirects to home page.
    Supports both POST (recommended) and GET for seamless user experience.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"You have been successfully logged out, {username}.")
    return redirect('store:product_list')
