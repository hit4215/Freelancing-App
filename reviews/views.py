from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from jobs.models import Contract

@login_required
def create_review_view(request, contract_id):
    contract = get_object_or_404(
        Contract.objects.select_related('client', 'freelancer', 'job'),
        id=contract_id
    )

    # Reviewer must be client or freelancer
    if request.user != contract.client and request.user != contract.freelancer:
        messages.error(request, "You are not authorized to review this contract.")
        return redirect('dashboard')

    # Determine reviewee
    reviewee = contract.freelancer if request.user == contract.client else contract.client

    # Check if already reviewed
    existing_review = Review.objects.filter(contract=contract, reviewer=request.user).first()
    if existing_review:
        messages.info(request, "You have already submitted a review for this contract.")
        return redirect('profile', username=reviewee.username)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.contract = contract
            review.reviewer = request.user
            review.reviewee = reviewee
            review.save()

            # In-App Notification to reviewee
            from core.services import send_notification
            from django.urls import reverse
            send_notification(
                recipient=reviewee,
                actor=request.user,
                notification_type='SYSTEM',
                title=f"New Review from {request.user.get_full_name() or request.user.username}",
                message=f"{request.user.get_full_name() or request.user.username} rated your collaboration {review.rating}/5 stars: \"{review.comment[:75]}...\"",
                link=reverse('profile', args=[reviewee.username])
            )

            messages.success(request, f"Review submitted for {reviewee.get_full_name() or reviewee.username}!")
            return redirect('profile', username=reviewee.username)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'contract': contract,
        'reviewee': reviewee,
    }
    return render(request, 'reviews/create_review.html', context)
