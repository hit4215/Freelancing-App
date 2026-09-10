from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from accounts.models import CustomUser, Skill
from jobs.models import Job, Category, Proposal, Contract, Invoice, SavedJob, JobInvitation, ContractMilestone
from messaging.models import Conversation, Message
from reviews.models import Review
from .models import Notification

def home_view(request):
    categories = Category.objects.annotate(job_count=Count('jobs')).all()[:8]
    featured_jobs = Job.objects.filter(status='OPEN').select_related('client', 'category').prefetch_related('skills').order_by('-created_at')[:6]
    top_freelancers = CustomUser.objects.filter(
        role__in=['FREELANCER', 'BOTH'],
        is_available_for_hire=True
    ).prefetch_related('skills').order_by('-job_success_score')[:6]

    stats = {
        'freelancers_count': CustomUser.objects.filter(role__in=['FREELANCER', 'BOTH']).count(),
        'jobs_count': Job.objects.count(),
        'active_contracts': Contract.objects.filter(status='ACTIVE').count(),
        'completed_contracts': Contract.objects.filter(status='COMPLETED').count(),
    }

    context = {
        'categories': categories,
        'featured_jobs': featured_jobs,
        'top_freelancers': top_freelancers,
        'stats': stats,
    }
    return render(request, 'core/home.html', context)


@login_required
def dashboard_view(request):
    user = request.user
    
    context = {'user': user}

    # Fetch user's invoices (both as client and freelancer)
    invoices = Invoice.objects.filter(
        Q(client=user) | Q(freelancer=user)
    ).select_related('contract__job', 'client', 'freelancer').order_by('-issue_date')

    if user.is_client:
        client_jobs = Job.objects.filter(client=user).prefetch_related('proposals', 'skills').order_by('-created_at')
        active_contracts = Contract.objects.filter(client=user, status='ACTIVE').select_related('freelancer', 'job')
        completed_contracts = Contract.objects.filter(client=user, status='COMPLETED').select_related('freelancer', 'job')
        total_proposals = Proposal.objects.filter(job__client=user).count()
        sent_invitations = JobInvitation.objects.filter(client=user).select_related('job', 'freelancer').order_by('-created_at')

        context.update({
            'client_jobs': client_jobs,
            'active_contracts': active_contracts,
            'completed_contracts': completed_contracts,
            'total_jobs_posted': client_jobs.count(),
            'total_proposals_received': total_proposals,
            'active_contracts_count': active_contracts.count(),
            'total_spent': user.total_spent,
            'sent_invitations': sent_invitations,
        })

    if user.is_freelancer:
        proposals = Proposal.objects.filter(freelancer=user).select_related('job__client', 'job__category').order_by('-created_at')
        active_contracts = Contract.objects.filter(freelancer=user, status='ACTIVE').select_related('client', 'job')
        completed_contracts = Contract.objects.filter(freelancer=user, status='COMPLETED').select_related('client', 'job')
        saved_jobs = SavedJob.objects.filter(user=user).select_related('job__client', 'job__category').order_by('-created_at')
        received_invitations = JobInvitation.objects.filter(freelancer=user).select_related('job__client', 'client').order_by('-created_at')
        
        # Recommended jobs matching skills
        user_skill_ids = user.skills.values_list('id', flat=True)
        recommended_jobs = Job.objects.filter(
            status='OPEN',
            skills__id__in=user_skill_ids
        ).exclude(proposals__freelancer=user).distinct()[:5]

        if not recommended_jobs.exists():
            recommended_jobs = Job.objects.filter(status='OPEN').exclude(proposals__freelancer=user).order_by('-created_at')[:5]

        context.update({
            'freelancer_proposals': proposals,
            'active_contracts': active_contracts,
            'completed_contracts': completed_contracts,
            'active_proposals_count': proposals.filter(status='PENDING').count(),
            'active_contracts_count': active_contracts.count(),
            'completed_contracts_count': completed_contracts.count(),
            'total_earned': user.total_earned,
            'recommended_jobs': recommended_jobs,
            'saved_jobs': saved_jobs,
            'received_invitations': received_invitations,
        })

    context['invoices'] = invoices
    return render(request, 'core/dashboard.html', context)


def freelancer_directory_view(request):
    freelancers = CustomUser.objects.filter(
        role__in=['FREELANCER', 'BOTH']
    ).prefetch_related('skills').order_by('-job_success_score')

    # Search keyword
    q = request.GET.get('q', '').strip()
    if q:
        freelancers = freelancers.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(headline__icontains=q) |
            Q(bio__icontains=q) |
            Q(skills__name__icontains=q)
        ).distinct()

    # Skill filter
    skill_filter = request.GET.get('skill', '').strip()
    if skill_filter:
        freelancers = freelancers.filter(skills__name__iexact=skill_filter)

    # Experience level
    experience = request.GET.get('experience', '').strip()
    if experience:
        freelancers = freelancers.filter(experience_level=experience)

    # Hourly rate range
    min_rate = request.GET.get('min_rate')
    max_rate = request.GET.get('max_rate')
    if min_rate:
        try:
            freelancers = freelancers.filter(hourly_rate__gte=float(min_rate))
        except ValueError:
            pass
    if max_rate:
        try:
            freelancers = freelancers.filter(hourly_rate__lte=float(max_rate))
        except ValueError:
            pass

    # Availability
    available_only = request.GET.get('available')
    if available_only:
        freelancers = freelancers.filter(is_available_for_hire=True)

    skills = Skill.objects.all()
    paginator = Paginator(freelancers, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'skills': skills,
        'search_query': q,
        'selected_skill': skill_filter,
        'selected_experience': experience,
        'min_rate': min_rate,
        'max_rate': max_rate,
        'total_freelancers_count': freelancers.count(),
    }
    return render(request, 'core/freelancers.html', context)


def how_it_works_view(request):
    return render(request, 'core/how_it_works.html')


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500_view(request):
    return render(request, '500.html', status=500)


@login_required
def platform_admin_view(request):
    """
    Executive Platform Command & Control Panel.
    Allows administrators to inspect every entry in the system (Users, Jobs, Proposals,
    Contracts, Messages, Reviews, Categories, Skills) and perform required management actions.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted. Platform Administrator privileges required.")
        return redirect('dashboard')

    # Handle Administrative POST Actions
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'toggle_user_availability':
            user_id = request.POST.get('user_id')
            target_user = get_object_or_404(CustomUser, id=user_id)
            target_user.is_available_for_hire = not target_user.is_available_for_hire
            target_user.save()
            messages.success(request, f"Availability for @{target_user.username} set to {target_user.is_available_for_hire}.")
            return redirect(f"{request.path}?tab=users")

        elif action == 'toggle_user_staff':
            user_id = request.POST.get('user_id')
            target_user = get_object_or_404(CustomUser, id=user_id)
            if target_user == request.user:
                messages.error(request, "You cannot alter your own staff administrator status.")
            else:
                target_user.is_staff = not target_user.is_staff
                target_user.save()
                messages.success(request, f"Staff access for @{target_user.username} set to {target_user.is_staff}.")
            return redirect(f"{request.path}?tab=users")

        elif action == 'update_job_status':
            job_id = request.POST.get('job_id')
            new_status = request.POST.get('status')
            job = get_object_or_404(Job, id=job_id)
            if new_status in dict(Job.STATUS_CHOICES):
                job.status = new_status
                job.save()
                messages.success(request, f"Job #{job.id} ('{job.title[:25]}...') status updated to {job.get_status_display()}.")
            return redirect(f"{request.path}?tab=jobs")

        elif action == 'update_proposal_status':
            proposal_id = request.POST.get('proposal_id')
            new_status = request.POST.get('status')
            proposal = get_object_or_404(Proposal, id=proposal_id)
            if new_status in dict(Proposal.STATUS_CHOICES):
                proposal.status = new_status
                proposal.save()
                messages.success(request, f"Proposal #{proposal.id} status updated to {proposal.get_status_display()}.")
            return redirect(f"{request.path}?tab=proposals")

        elif action == 'complete_contract':
            from django.utils import timezone
            contract_id = request.POST.get('contract_id')
            contract = get_object_or_404(Contract, id=contract_id)
            contract.status = 'COMPLETED'
            contract.completed_at = timezone.now()
            contract.save()
            messages.success(request, f"Contract #{contract.id} ({contract.job.title[:25]}) marked as COMPLETED.")
            return redirect(f"{request.path}?tab=contracts")

        elif action == 'cancel_contract':
            contract_id = request.POST.get('contract_id')
            contract = get_object_or_404(Contract, id=contract_id)
            contract.status = 'CANCELLED'
            contract.save()
            messages.warning(request, f"Contract #{contract.id} marked as CANCELLED.")
            return redirect(f"{request.path}?tab=contracts")

        elif action == 'delete_review':
            review_id = request.POST.get('review_id')
            review = get_object_or_404(Review, id=review_id)
            review.delete()
            messages.success(request, f"Review #{review_id} has been moderated and removed from the platform.")
            return redirect(f"{request.path}?tab=reviews")

        elif action == 'add_category':
            name = request.POST.get('name', '').strip()
            icon = request.POST.get('icon', 'fa-solid fa-briefcase').strip()
            desc = request.POST.get('description', '').strip()
            if name:
                cat, created = Category.objects.get_or_create(name=name, defaults={'icon': icon, 'description': desc})
                if created:
                    messages.success(request, f"New Category '{name}' created successfully.")
                else:
                    messages.info(request, f"Category '{name}' already exists.")
            return redirect(f"{request.path}?tab=taxonomy")

        elif action == 'add_skill':
            name = request.POST.get('name', '').strip()
            category_name = request.POST.get('category', 'General').strip()
            if name:
                skill, created = Skill.objects.get_or_create(name=name, defaults={'category': category_name})
                if created:
                    messages.success(request, f"New Skill '{name}' added successfully.")
                else:
                    messages.info(request, f"Skill '{name}' already exists.")
            return redirect(f"{request.path}?tab=taxonomy")

    # Current tab
    active_tab = request.GET.get('tab', 'overview')

    # Aggregated Platform Metrics
    total_users = CustomUser.objects.count()
    freelancers_count = CustomUser.objects.filter(role__in=['FREELANCER', 'BOTH']).count()
    clients_count = CustomUser.objects.filter(role__in=['CLIENT', 'BOTH']).count()
    staff_count = CustomUser.objects.filter(is_staff=True).count()

    total_jobs = Job.objects.count()
    open_jobs = Job.objects.filter(status='OPEN').count()
    in_progress_jobs = Job.objects.filter(status='IN_PROGRESS').count()
    completed_jobs = Job.objects.filter(status='COMPLETED').count()
    closed_jobs = Job.objects.filter(status='CLOSED').count()

    total_proposals = Proposal.objects.count()
    accepted_proposals = Proposal.objects.filter(status='ACCEPTED').count()
    pending_proposals = Proposal.objects.filter(status='PENDING').count()

    total_contracts = Contract.objects.count()
    active_contracts = Contract.objects.filter(status='ACTIVE').count()
    completed_contracts = Contract.objects.filter(status='COMPLETED').count()

    gmv_agg = Contract.objects.aggregate(total_gmv=Sum('total_amount'))
    total_gmv = gmv_agg['total_gmv'] or 0

    total_conversations = Conversation.objects.count()
    total_messages = Message.objects.count()

    total_reviews = Review.objects.count()
    avg_rating_agg = Review.objects.aggregate(avg=Avg('rating'))
    avg_rating = round(avg_rating_agg['avg'] or 5.0, 1)

    # Search & Filtering
    user_q = request.GET.get('user_q', '').strip()
    user_role = request.GET.get('user_role', '').strip()
    users_qs = CustomUser.objects.all().prefetch_related('skills').order_by('-date_joined')
    if user_q:
        users_qs = users_qs.filter(
            Q(username__icontains=user_q) |
            Q(email__icontains=user_q) |
            Q(first_name__icontains=user_q) |
            Q(last_name__icontains=user_q)
        )
    if user_role:
        users_qs = users_qs.filter(role=user_role)

    job_q = request.GET.get('job_q', '').strip()
    job_status = request.GET.get('job_status', '').strip()
    jobs_qs = Job.objects.select_related('client', 'category').prefetch_related('proposals', 'skills').order_by('-created_at')
    if job_q:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=job_q) |
            Q(client__username__icontains=job_q) |
            Q(category__name__icontains=job_q)
        )
    if job_status:
        jobs_qs = jobs_qs.filter(status=job_status)

    prop_q = request.GET.get('prop_q', '').strip()
    proposals_qs = Proposal.objects.select_related('job', 'freelancer').order_by('-created_at')
    if prop_q:
        proposals_qs = proposals_qs.filter(
            Q(job__title__icontains=prop_q) |
            Q(freelancer__username__icontains=prop_q)
        )

    contract_q = request.GET.get('contract_q', '').strip()
    contracts_qs = Contract.objects.select_related('job', 'client', 'freelancer').order_by('-created_at')
    if contract_q:
        contracts_qs = contracts_qs.filter(
            Q(job__title__icontains=contract_q) |
            Q(client__username__icontains=contract_q) |
            Q(freelancer__username__icontains=contract_q)
        )

    msg_q = request.GET.get('msg_q', '').strip()
    messages_qs = Message.objects.select_related('sender', 'conversation').order_by('-created_at')
    if msg_q:
        messages_qs = messages_qs.filter(
            Q(body__icontains=msg_q) |
            Q(sender__username__icontains=msg_q)
        )
    messages_qs = messages_qs[:60]

    rev_q = request.GET.get('rev_q', '').strip()
    reviews_qs = Review.objects.select_related('reviewer', 'reviewee', 'contract__job').order_by('-created_at')
    if rev_q:
        reviews_qs = reviews_qs.filter(
            Q(reviewer__username__icontains=rev_q) |
            Q(reviewee__username__icontains=rev_q) |
            Q(comment__icontains=rev_q)
        )

    categories = Category.objects.annotate(job_count=Count('jobs')).order_by('name')
    skills = Skill.objects.annotate(user_count=Count('users')).order_by('name')

    context = {
        'active_tab': active_tab,
        'stats': {
            'total_users': total_users,
            'freelancers_count': freelancers_count,
            'clients_count': clients_count,
            'staff_count': staff_count,
            'total_jobs': total_jobs,
            'open_jobs': open_jobs,
            'in_progress_jobs': in_progress_jobs,
            'completed_jobs': completed_jobs,
            'closed_jobs': closed_jobs,
            'total_proposals': total_proposals,
            'accepted_proposals': accepted_proposals,
            'pending_proposals': pending_proposals,
            'total_contracts': total_contracts,
            'active_contracts': active_contracts,
            'completed_contracts': completed_contracts,
            'total_gmv': total_gmv,
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_reviews': total_reviews,
            'avg_rating': avg_rating,
        },
        'users_list': users_qs,
        'user_q': user_q,
        'user_role': user_role,
        'jobs_list': jobs_qs,
        'job_q': job_q,
        'job_status': job_status,
        'proposals_list': proposals_qs,
        'prop_q': prop_q,
        'contracts_list': contracts_qs,
        'contract_q': contract_q,
        'messages_list': messages_qs,
        'msg_q': msg_q,
        'reviews_list': reviews_qs,
        'rev_q': rev_q,
        'categories': categories,
        'skills': skills,
    }
    return render(request, 'core/platform_admin.html', context)


def admin_gateway_view(request):
    """
    Platform Administrator Access & Authentication Gateway.
    - Verified staff / superusers are smoothly redirected into the Executive Command Center.
    - Allows direct administrative authentication via dedicated secure login form.
    - Displays high-level platform health, administrative metrics, and account switcher options.
    """
    from django.contrib.auth import authenticate, login
    from django.conf import settings

    # If the user is already authenticated as staff/superuser and didn't request the hub preview
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        if not request.GET.get('stay'):
            return redirect('platform_admin')

    # Handle administrative direct login submission
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both administrator username and password.")
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    messages.success(request, f"Welcome back, Administrator @{user.username}! Command Center access authorized.")
                    return redirect('platform_admin')
                else:
                    messages.error(
                        request,
                        f"Access Denied: Account @{user.username} is authenticated as a standard user ({user.get_role_display()}), but does not possess platform administrator privileges."
                    )
            else:
                messages.error(request, "Invalid administrator credentials. Please check your username and password.")

    # High-level system overview stats for the gateway
    gateway_stats = {
        'total_users': CustomUser.objects.count(),
        'total_staff': CustomUser.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count(),
        'total_jobs': Job.objects.count(),
        'active_contracts': Contract.objects.filter(status='ACTIVE').count(),
        'completed_contracts': Contract.objects.filter(status='COMPLETED').count(),
        'db_status': 'Operational',
    }

    # Available staff accounts in development (for fast local onboarding/testing)
    staff_dev_accounts = []
    if settings.DEBUG:
        staff_dev_accounts = list(
            CustomUser.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).values_list('username', flat=True)[:4]
        )

    context = {
        'stats': gateway_stats,
        'staff_dev_accounts': staff_dev_accounts,
        'debug_mode': settings.DEBUG,
    }
    return render(request, 'core/admin_gateway.html', context)


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user).select_related('actor')

    # Optional filter by notification type
    notif_type = request.GET.get('type')
    if notif_type:
        notifications = notifications.filter(notification_type=notif_type)

    # Optional filter by read/unread status
    status_filter = request.GET.get('status')
    if status_filter == 'unread':
        notifications = notifications.filter(is_read=False)

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'active_type': notif_type or 'all',
        'active_status': status_filter or 'all',
    }
    return render(request, 'core/notifications.html', context)


@login_required
def mark_notification_read_view(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications_list')


@login_required
def mark_all_notifications_read_view(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications have been marked as read.")
    referer = request.META.get('HTTP_REFERER')
    if referer and 'notifications' not in referer:
        return redirect(referer)
    return redirect('notifications_list')



