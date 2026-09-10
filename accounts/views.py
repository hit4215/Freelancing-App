from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm, PortfolioItemForm
from .models import CustomUser, PortfolioItem, SavedFreelancer
from jobs.models import Job

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to LancerPulse, {user.first_name}! Your account is ready.")
            return redirect('dashboard')
    else:
        initial_role = request.GET.get('role', 'FREELANCER')
        form = CustomUserCreationForm(initial={'role': initial_role})

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


def profile_view(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    portfolio_items = profile_user.portfolio_items.all()
    reviews = profile_user.received_reviews.select_related('reviewer').all()
    posted_jobs = profile_user.posted_jobs.filter(status='OPEN') if profile_user.is_client else []
    
    is_saved = False
    client_open_jobs = []
    if request.user.is_authenticated:
        is_saved = SavedFreelancer.objects.filter(user=request.user, freelancer=profile_user).exists()
        if request.user.is_client:
            client_open_jobs = Job.objects.filter(client=request.user, status='OPEN')

    context = {
        'profile_user': profile_user,
        'portfolio_items': portfolio_items,
        'reviews': reviews,
        'posted_jobs': posted_jobs,
        'is_saved': is_saved,
        'client_open_jobs': client_open_jobs,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def toggle_save_freelancer_view(request, freelancer_id):
    freelancer = get_object_or_404(CustomUser, id=freelancer_id)
    if freelancer == request.user:
        messages.warning(request, "You cannot bookmark your own profile.")
        return redirect('profile', username=freelancer.username)

    saved = SavedFreelancer.objects.filter(user=request.user, freelancer=freelancer).first()
    if saved:
        saved.delete()
        messages.info(request, f"Removed @{freelancer.username} from your saved freelancers.")
    else:
        SavedFreelancer.objects.create(user=request.user, freelancer=freelancer)
        messages.success(request, f"Saved @{freelancer.username} to your talent list!")

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('profile', username=freelancer.username)



@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user)

    portfolio_form = PortfolioItemForm()
    portfolio_items = request.user.portfolio_items.all()

    context = {
        'form': form,
        'portfolio_form': portfolio_form,
        'portfolio_items': portfolio_items,
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def add_portfolio_view(request):
    if request.method == 'POST':
        form = PortfolioItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, f"Portfolio item '{item.title}' added!")
        else:
            messages.error(request, "Please correct the errors in the portfolio form.")
    return redirect('edit_profile')


@login_required
def delete_portfolio_view(request, pk):
    item = get_object_or_404(PortfolioItem, pk=pk, user=request.user)
    item.delete()
    messages.success(request, "Portfolio item removed.")
    return redirect('edit_profile')
