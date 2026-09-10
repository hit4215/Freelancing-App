import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from accounts.models import CustomUser
from .models import Job, Proposal, Category, Contract, ContractMilestone, Invoice, SavedJob, JobInvitation
from .forms import JobForm, ProposalForm, ContractMilestoneForm, MilestoneSubmissionForm, JobInvitationForm
from messaging.models import Conversation, Message
from core.services import send_notification

def job_list_view(request):
    # Filter by project status (default to OPEN for active bidding, or allow ALL, IN_PROGRESS, COMPLETED, CLOSED)
    status_filter = request.GET.get('status', 'OPEN').strip()
    if status_filter == 'ALL':
        jobs = Job.objects.all().select_related('client', 'category').prefetch_related('skills')
    elif status_filter in dict(Job.STATUS_CHOICES):
        jobs = Job.objects.filter(status=status_filter).select_related('client', 'category').prefetch_related('skills')
    else:
        status_filter = 'OPEN'
        jobs = Job.objects.filter(status='OPEN').select_related('client', 'category').prefetch_related('skills')

    # Filter by search query
    q = request.GET.get('q', '').strip()
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(skills__name__icontains=q)
        ).distinct()

    # Filter by category
    category_slug = request.GET.get('category', '').strip()
    if category_slug:
        jobs = jobs.filter(category__slug=category_slug)

    # Filter by budget type
    budget_type = request.GET.get('budget_type', '').strip()
    if budget_type:
        jobs = jobs.filter(budget_type=budget_type)

    # Filter by experience
    experience = request.GET.get('experience', '').strip()
    if experience:
        jobs = jobs.filter(experience_level=experience)

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'budget_high':
        jobs = jobs.order_by('-budget_max')
    elif sort == 'budget_low':
        jobs = jobs.order_by('budget_min')
    else:
        jobs = jobs.order_by('-created_at')

    categories = Category.objects.all()
    paginator = Paginator(jobs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    saved_job_ids = set()
    if request.user.is_authenticated:
        saved_job_ids = set(SavedJob.objects.filter(user=request.user).values_list('job_id', flat=True))

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'selected_budget_type': budget_type,
        'selected_experience': experience,
        'selected_status': status_filter,
        'status_choices': Job.STATUS_CHOICES,
        'search_query': q,
        'selected_sort': sort,
        'total_jobs_count': jobs.count(),
        'saved_job_ids': saved_job_ids,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail_view(request, slug):
    job = get_object_or_404(
        Job.objects.select_related('client', 'category').prefetch_related('skills', 'proposals__freelancer'),
        slug=slug
    )

    user_proposal = None
    is_saved = False
    if request.user.is_authenticated:
        user_proposal = job.proposals.filter(freelancer=request.user).first()
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()

    proposal_form = ProposalForm()
    proposals = job.proposals.select_related('freelancer').all() if (request.user.is_authenticated and (request.user == job.client or request.user.is_staff)) else []

    contract = getattr(job, 'contract', None)

    context = {
        'job': job,
        'user_proposal': user_proposal,
        'proposal_form': proposal_form,
        'proposals': proposals,
        'contract': contract,
        'is_client_owner': request.user.is_authenticated and request.user == job.client,
        'is_saved': is_saved,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def create_job_view(request):
    if not request.user.is_client:
        messages.warning(request, "Only clients can post new jobs. Please update your profile role.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user
            if not job.status:
                job.status = 'OPEN'
            job.save()
            form.save_m2m()  # save skills
            messages.success(request, f"Job '{job.title}' posted successfully!")
            return redirect('job_detail', slug=job.slug)
    else:
        form = JobForm(initial={'status': 'OPEN'})

    return render(request, 'jobs/create_job.html', {'form': form, 'is_edit': False})


@login_required
def edit_job_view(request, slug):
    job = get_object_or_404(Job, slug=slug, client=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save()
            messages.success(request, "Job updated successfully!")
            return redirect('job_detail', slug=job.slug)
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/create_job.html', {'form': form, 'job': job, 'is_edit': True})


@login_required
def submit_proposal_view(request, slug):
    job = get_object_or_404(Job, slug=slug)

    if not request.user.is_freelancer:
        messages.error(request, "Only freelancers can submit proposals.")
        return redirect('job_detail', slug=slug)

    if job.status != 'OPEN':
        messages.error(request, f"This project is currently {job.get_status_display().lower()} and not accepting new proposals.")
        return redirect('job_detail', slug=slug)

    if job.client == request.user:
        messages.error(request, "You cannot bid on your own job.")
        return redirect('job_detail', slug=slug)

    if Proposal.objects.filter(job=job, freelancer=request.user).exists():
        messages.warning(request, "You have already submitted a proposal for this job.")
        return redirect('job_detail', slug=slug)

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.job = job
            proposal.freelancer = request.user
            proposal.save()

            # Auto-initiate conversation with client
            conv = Conversation.objects.filter(participants=job.client).filter(participants=request.user).first()
            if not conv:
                conv = Conversation.objects.create(
                    subject=f"Proposal: {job.title[:60]}",
                    job=job
                )
                conv.participants.add(request.user, job.client)

            Message.objects.create(
                conversation=conv,
                sender=request.user,
                body=f"Hello! I have submitted a proposal for '{job.title}' with a bid of ${proposal.bid_amount:.2f} (Delivery in {proposal.estimated_days} days).\n\nCover Letter excerpt:\n{proposal.cover_letter[:200]}..."
            )

            # In-App Notification to client
            send_notification(
                recipient=job.client,
                actor=request.user,
                notification_type='PROPOSAL',
                title=f"New Proposal for '{job.title[:40]}'",
                message=f"{request.user.get_full_name() or request.user.username} submitted a proposal for ${proposal.bid_amount:.2f}.",
                link=reverse('job_detail', args=[job.slug])
            )

            messages.success(request, "Your proposal and introductory message were submitted successfully!")
            return redirect('job_detail', slug=slug)
    
    return redirect('job_detail', slug=slug)


@login_required
def accept_proposal_view(request, proposal_id):
    proposal = get_object_or_404(Proposal.objects.select_related('job', 'freelancer'), id=proposal_id)
    job = proposal.job

    if job.client != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to accept this proposal.")
        return redirect('job_detail', slug=job.slug)

    if job.status != 'OPEN':
        messages.warning(request, "This job is already active or completed.")
        return redirect('job_detail', slug=job.slug)

    # Accept this proposal, reject others
    proposal.status = 'ACCEPTED'
    proposal.save()

    job.proposals.exclude(id=proposal.id).update(status='REJECTED')
    job.status = 'IN_PROGRESS'
    job.save()

    # Create Contract
    contract, created = Contract.objects.get_or_create(
        job=job,
        defaults={
            'proposal': proposal,
            'client': request.user,
            'freelancer': proposal.freelancer,
            'total_amount': proposal.bid_amount,
            'status': 'ACTIVE'
        }
    )

    # Create default first milestone if none exist
    if contract.milestones.count() == 0:
        ContractMilestone.objects.create(
            contract=contract,
            title=f"Project Milestone 1: Core Deliverables",
            description=f"Full scope implementation for {job.title}",
            amount=contract.total_amount,
            order=1,
            status='PENDING'
        )

    # Conversation message notify
    conv = Conversation.objects.filter(participants=request.user).filter(participants=proposal.freelancer).first()
    if not conv:
        conv = Conversation.objects.create(subject=f"Contract: {job.title}", job=job)
        conv.participants.add(request.user, proposal.freelancer)
    
    Message.objects.create(
        conversation=conv,
        sender=request.user,
        body=f"Congratulations {proposal.freelancer.first_name or proposal.freelancer.username}! Your proposal for '{job.title}' has been accepted. The contract of ${contract.total_amount:.2f} is now active."
    )

    # In-App Notification to Freelancer
    send_notification(
        recipient=proposal.freelancer,
        actor=request.user,
        notification_type='CONTRACT',
        title=f"Proposal Accepted: {job.title[:40]}",
        message=f"Congratulations! Your proposal for '{job.title}' was accepted. Contract workspace is now active.",
        link=reverse('contract_detail', args=[contract.id])
    )

    messages.success(request, f"You hired {proposal.freelancer.get_full_name() or proposal.freelancer.username}! Contract is now active.")
    return redirect('job_detail', slug=job.slug)


@login_required
def complete_contract_view(request, contract_id):
    contract = get_object_or_404(Contract.objects.select_related('job', 'client', 'freelancer'), id=contract_id)

    if request.user != contract.client and request.user != contract.freelancer and not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    if contract.status == 'ACTIVE':
        contract.status = 'COMPLETED'
        contract.completed_at = timezone.now()
        contract.save()

        contract.job.status = 'COMPLETED'
        contract.job.save()

        # Update financials if not already covered by milestones
        freelancer = contract.freelancer
        client = contract.client

        unpaid_amount = contract.total_amount - contract.paid_amount
        if unpaid_amount > 0:
            freelancer.total_earned += unpaid_amount
            freelancer.save(update_fields=['total_earned'])
            client.total_spent += unpaid_amount
            client.save(update_fields=['total_spent'])

            # Generate final invoice
            inv_num = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            fee = round(unpaid_amount * Decimal('0.05'), 2)
            Invoice.objects.create(
                invoice_number=inv_num,
                contract=contract,
                client=client,
                freelancer=freelancer,
                amount=unpaid_amount,
                service_fee=fee,
                total=unpaid_amount,
                status='PAID',
                notes=f"Final settlement for contract: {contract.job.title}"
            )

        # Notify partner
        partner = contract.freelancer if request.user == contract.client else contract.client
        send_notification(
            recipient=partner,
            actor=request.user,
            notification_type='CONTRACT',
            title=f"Contract Finalized: {contract.job.title[:40]}",
            message=f"Contract '{contract.job.title}' has been marked completed. Please leave a client/freelancer review!",
            link=reverse('create_review', args=[contract.id])
        )

        messages.success(request, f"Contract for '{contract.job.title}' marked as completed! Please leave a review.")
        return redirect('create_review', contract_id=contract.id)

    return redirect('contract_detail', contract_id=contract.id)


@login_required
def contract_detail_view(request, contract_id):
    contract = get_object_or_404(
        Contract.objects.select_related('job', 'client', 'freelancer', 'proposal').prefetch_related('milestones', 'invoices'),
        id=contract_id
    )

    if request.user != contract.client and request.user != contract.freelancer and not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this contract workspace.")
        return redirect('dashboard')

    milestones = contract.milestones.all().order_by('order', 'created_at')
    invoices = contract.invoices.all().order_by('-issue_date')

    milestone_form = ContractMilestoneForm()
    submission_form = MilestoneSubmissionForm()

    is_client = (request.user == contract.client)
    is_freelancer = (request.user == contract.freelancer)

    paid_amount = contract.paid_amount
    remaining_amount = max(Decimal('0.00'), contract.total_amount - paid_amount)

    context = {
        'contract': contract,
        'milestones': milestones,
        'invoices': invoices,
        'milestone_form': milestone_form,
        'submission_form': submission_form,
        'is_client': is_client,
        'is_freelancer': is_freelancer,
        'paid_amount': paid_amount,
        'remaining_amount': remaining_amount,
    }
    return render(request, 'jobs/contract_detail.html', context)


@login_required
def add_milestone_view(request, contract_id):
    contract = get_object_or_404(Contract, id=contract_id)
    if request.user != contract.client and not request.user.is_staff:
        messages.error(request, "Only the client can add new milestones.")
        return redirect('contract_detail', contract_id=contract.id)

    if request.method == 'POST':
        form = ContractMilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.contract = contract
            milestone.status = 'PENDING'
            milestone.save()

            send_notification(
                recipient=contract.freelancer,
                actor=request.user,
                notification_type='CONTRACT',
                title=f"New Milestone Added: {milestone.title[:45]}",
                message=f"Client added milestone '{milestone.title}' (${milestone.amount:.2f}) to contract '{contract.job.title}'.",
                link=reverse('contract_detail', args=[contract.id])
            )

            messages.success(request, f"Milestone '{milestone.title}' added successfully!")
        else:
            messages.error(request, "Please check milestone form entries.")

    return redirect('contract_detail', contract_id=contract.id)


@login_required
def submit_milestone_view(request, milestone_id):
    milestone = get_object_or_404(
        ContractMilestone.objects.select_related('contract__client', 'contract__freelancer', 'contract__job'),
        id=milestone_id
    )
    contract = milestone.contract

    if request.user != contract.freelancer and not request.user.is_staff:
        messages.error(request, "Only the assigned freelancer can submit work for this milestone.")
        return redirect('contract_detail', contract_id=contract.id)

    if request.method == 'POST':
        notes = request.POST.get('submission_notes', '').strip()
        url = request.POST.get('submission_url', '').strip()

        milestone.submission_notes = notes
        milestone.submission_url = url
        milestone.status = 'SUBMITTED'
        milestone.submitted_at = timezone.now()
        milestone.save()

        send_notification(
            recipient=contract.client,
            actor=request.user,
            notification_type='CONTRACT',
            title=f"Work Submitted: {milestone.title[:45]}",
            message=f"{request.user.get_full_name() or request.user.username} submitted deliverables for '{milestone.title}'. Please review.",
            link=reverse('contract_detail', args=[contract.id])
        )

        messages.success(request, f"Deliverables for '{milestone.title}' submitted for review!")

    return redirect('contract_detail', contract_id=contract.id)


@login_required
def approve_milestone_view(request, milestone_id):
    milestone = get_object_or_404(
        ContractMilestone.objects.select_related('contract__client', 'contract__freelancer', 'contract__job'),
        id=milestone_id
    )
    contract = milestone.contract

    if request.user != contract.client and not request.user.is_staff:
        messages.error(request, "Only the client can approve milestone releases.")
        return redirect('contract_detail', contract_id=contract.id)

    if milestone.status == 'APPROVED':
        messages.info(request, "This milestone has already been approved.")
        return redirect('contract_detail', contract_id=contract.id)

    milestone.status = 'APPROVED'
    milestone.approved_at = timezone.now()
    milestone.save()

    # Create Invoice for this milestone release
    inv_num = f"INV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    fee = round(milestone.amount * Decimal('0.05'), 2)
    invoice = Invoice.objects.create(
        invoice_number=inv_num,
        contract=contract,
        client=contract.client,
        freelancer=contract.freelancer,
        amount=milestone.amount,
        service_fee=fee,
        total=milestone.amount,
        status='PAID',
        notes=f"Approved milestone escrow release: {milestone.title}"
    )

    # Update financials
    contract.freelancer.total_earned += milestone.amount
    contract.freelancer.save(update_fields=['total_earned'])
    contract.client.total_spent += milestone.amount
    contract.client.save(update_fields=['total_spent'])

    # Check if all milestones are completed
    pending_milestones = contract.milestones.exclude(status='APPROVED').exists()
    if not pending_milestones and contract.status == 'ACTIVE':
        contract.status = 'COMPLETED'
        contract.completed_at = timezone.now()
        contract.save(update_fields=['status', 'completed_at'])
        contract.job.status = 'COMPLETED'
        contract.job.save(update_fields=['status'])

    send_notification(
        recipient=contract.freelancer,
        actor=request.user,
        notification_type='PAYMENT',
        title=f"Funds Released: ${milestone.amount:.2f}",
        message=f"Client approved milestone '{milestone.title}' and released ${milestone.amount:.2f} (Invoice #{invoice.invoice_number}).",
        link=reverse('invoice_detail', args=[invoice.id])
    )

    messages.success(request, f"Milestone '{milestone.title}' approved! ${milestone.amount:.2f} released. Invoice #{invoice.invoice_number} generated.")
    return redirect('contract_detail', contract_id=contract.id)


@login_required
def request_revision_view(request, milestone_id):
    milestone = get_object_or_404(
        ContractMilestone.objects.select_related('contract__client', 'contract__freelancer', 'contract__job'),
        id=milestone_id
    )
    contract = milestone.contract

    if request.user != contract.client and not request.user.is_staff:
        messages.error(request, "Only the client can request revisions.")
        return redirect('contract_detail', contract_id=contract.id)

    if request.method == 'POST':
        revision_notes = request.POST.get('revision_notes', '').strip()
        milestone.status = 'REVISION_REQUESTED'
        if revision_notes:
            milestone.submission_notes = f"{milestone.submission_notes}\n\n[Client Revision Feedback]: {revision_notes}".strip()
        milestone.save()

        send_notification(
            recipient=contract.freelancer,
            actor=request.user,
            notification_type='CONTRACT',
            title=f"Revision Requested: {milestone.title[:45]}",
            message=f"Client requested revision on '{milestone.title}': {revision_notes[:120]}",
            link=reverse('contract_detail', args=[contract.id])
        )

        messages.info(request, f"Revision requested for milestone '{milestone.title}'. Freelancer notified.")

    return redirect('contract_detail', contract_id=contract.id)


@login_required
def invoice_detail_view(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related('contract__job', 'client', 'freelancer'),
        id=invoice_id
    )

    if request.user != invoice.client and request.user != invoice.freelancer and not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this invoice.")
        return redirect('dashboard')

    context = {
        'invoice': invoice,
        'contract': invoice.contract,
    }
    return render(request, 'jobs/invoice_detail.html', context)


@login_required
def toggle_save_job_view(request, slug):
    job = get_object_or_404(Job, slug=slug)
    saved = SavedJob.objects.filter(user=request.user, job=job).first()

    if saved:
        saved.delete()
        is_saved = False
        msg = f"'{job.title[:30]}...' removed from your saved jobs."
    else:
        SavedJob.objects.create(user=request.user, job=job)
        is_saved = True
        msg = f"'{job.title[:30]}...' saved to your bookmarks."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return JsonResponse({'status': 'success', 'saved': is_saved, 'message': msg})

    messages.success(request, msg)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('job_detail', slug=slug)


@login_required
def invite_freelancer_view(request, freelancer_id):
    freelancer = get_object_or_404(CustomUser, id=freelancer_id)

    if not request.user.is_client and not request.user.is_staff:
        messages.error(request, "Only clients can invite talent to open jobs.")
        return redirect('profile', username=freelancer.username)

    if request.method == 'POST':
        form = JobInvitationForm(request.POST, client=request.user)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.client = request.user
            invitation.freelancer = freelancer

            existing = JobInvitation.objects.filter(job=invitation.job, freelancer=freelancer).first()
            if existing:
                messages.warning(request, f"You have already sent an invitation to {freelancer.get_full_name() or freelancer.username} for this job.")
            else:
                invitation.save()
                send_notification(
                    recipient=freelancer,
                    actor=request.user,
                    notification_type='INVITATION',
                    title=f"Job Invitation from {request.user.get_full_name() or request.user.username}",
                    message=f"You have been invited to submit a proposal for '{invitation.job.title}'.",
                    link=reverse('job_detail', args=[invitation.job.slug])
                )
                messages.success(request, f"Invitation sent to {freelancer.get_full_name() or freelancer.username}!")
        else:
            messages.error(request, "Please select an open job to invite this freelancer to.")

    return redirect('profile', username=freelancer.username)


@login_required
def respond_invitation_view(request, invitation_id, action):
    invitation = get_object_or_404(
        JobInvitation.objects.select_related('job', 'client'),
        id=invitation_id,
        freelancer=request.user
    )

    if action == 'accept':
        invitation.status = 'ACCEPTED'
        invitation.save()
        send_notification(
            recipient=invitation.client,
            actor=request.user,
            notification_type='INVITATION',
            title="Invitation Accepted!",
            message=f"{request.user.get_full_name() or request.user.username} accepted your invitation to apply for '{invitation.job.title}'.",
            link=reverse('job_detail', args=[invitation.job.slug])
        )
        messages.success(request, f"Invitation accepted! Please submit your proposal for '{invitation.job.title}'.")
        return redirect('job_detail', slug=invitation.job.slug)
    elif action == 'decline':
        invitation.status = 'DECLINED'
        invitation.save()
        send_notification(
            recipient=invitation.client,
            actor=request.user,
            notification_type='INVITATION',
            title="Invitation Declined",
            message=f"{request.user.get_full_name() or request.user.username} declined your invitation for '{invitation.job.title}'.",
            link=reverse('job_detail', args=[invitation.job.slug])
        )
    return redirect('dashboard')


@login_required
def update_job_status_view(request, slug):
    job = get_object_or_404(Job, slug=slug)

    if request.user != job.client and not request.user.is_staff:
        messages.error(request, "You do not have permission to change this project's status.")
        return redirect('job_detail', slug=job.slug)

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        valid_statuses = [c[0] for c in Job.STATUS_CHOICES]
        if new_status in valid_statuses:
            old_status = job.status
            job.status = new_status
            job.save()

            # Handle related contract updates if status changes to COMPLETED or CLOSED
            contract = getattr(job, 'contract', None)
            if new_status == 'COMPLETED':
                if contract and contract.status == 'ACTIVE':
                    contract.status = 'COMPLETED'
                    contract.completed_at = timezone.now()
                    contract.save()
                    send_notification(
                        recipient=contract.freelancer,
                        actor=request.user,
                        notification_type='CONTRACT',
                        title=f"Project Completed: {job.title[:40]}",
                        message=f"The project '{job.title}' has been marked as Completed.",
                        link=reverse('contract_detail', args=[contract.id])
                    )
            elif new_status == 'CLOSED':
                if contract and contract.status == 'ACTIVE':
                    send_notification(
                        recipient=contract.freelancer,
                        actor=request.user,
                        notification_type='CONTRACT',
                        title=f"Project Closed: {job.title[:40]}",
                        message=f"The project '{job.title}' was closed by the client.",
                        link=reverse('job_detail', args=[job.slug])
                    )

            messages.success(request, f"Project status changed from {dict(Job.STATUS_CHOICES).get(old_status)} to {job.get_status_display()}.")
        else:
            messages.error(request, "Invalid project status selected.")

    return redirect('job_detail', slug=job.slug)
