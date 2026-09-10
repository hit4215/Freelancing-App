from django.db import models
from django.conf import settings
from django.utils.text import slugify
from accounts.models import Skill

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=60, default="fa-solid fa-briefcase", help_text="FontAwesome icon class")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Job(models.Model):
    BUDGET_TYPE_CHOICES = (
        ('FIXED', 'Fixed Price'),
        ('HOURLY', 'Hourly Rate'),
    )

    EXPERIENCE_CHOICES = (
        ('ENTRY', 'Entry Level'),
        ('INTERMEDIATE', 'Intermediate'),
        ('EXPERT', 'Expert'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open for Bids'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CLOSED', 'Closed'),
    )

    LOCATION_CHOICES = (
        ('REMOTE', 'Remote Only'),
        ('HYBRID', 'Hybrid'),
        ('ONSITE', 'Onsite'),
    )

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')
    description = models.TextField()
    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES, default='FIXED')
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='INTERMEDIATE')
    location_type = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='REMOTE')
    skills = models.ManyToManyField(Skill, blank=True, related_name='jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    deadline_days = models.PositiveIntegerField(default=14, help_text="Estimated project timeline in days")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def proposal_count(self):
        return self.proposals.count()

    @property
    def budget_display(self):
        if self.budget_type == 'HOURLY':
            return f"${self.budget_min:.0f} - ${self.budget_max:.0f} / hr"
        if self.budget_min == self.budget_max:
            return f"${self.budget_min:.0f} (Fixed)"
        return f"${self.budget_min:.0f} - ${self.budget_max:.0f} (Fixed)"

    def __str__(self):
        return self.title


class Proposal(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('ACCEPTED', 'Hired / Accepted'),
        ('REJECTED', 'Declined'),
        ('WITHDRAWN', 'Withdrawn'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='proposals')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_proposals')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField(default=7)
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'freelancer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.freelancer.username}'s proposal for {self.job.title}"


class Contract(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active / In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='contract')
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='contracts')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_contracts')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_contracts')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def milestone_count(self):
        return self.milestones.count()

    @property
    def completed_milestones_count(self):
        return self.milestones.filter(status='APPROVED').count()

    @property
    def progress_percent(self):
        total = self.milestones.count()
        if total == 0:
            return 100 if self.status == 'COMPLETED' else 0
        approved = self.completed_milestones_count
        return int((approved / total) * 100)

    @property
    def paid_amount(self):
        approved = self.milestones.filter(status='APPROVED')
        total = sum(m.amount for m in approved)
        return total

    def __str__(self):
        return f"Contract: {self.job.title} ({self.status})"


class ContractMilestone(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Funded / In Progress'),
        ('SUBMITTED', 'Submitted for Review'),
        ('APPROVED', 'Approved & Released'),
        ('REVISION_REQUESTED', 'Revision Requested'),
    )

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='PENDING')
    submission_notes = models.TextField(blank=True, default='')
    submission_url = models.URLField(blank=True, default='')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Milestone: {self.title} - ${self.amount} ({self.status})"


class JobInvitation(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='invitations')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_invitations')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'freelancer')
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation: {self.freelancer.username} to {self.job.title}"


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('PAID', 'Paid'),
        ('ISSUED', 'Issued / Pending Settlement'),
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='invoices')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_invoices')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID')
    issue_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"Invoice #{self.invoice_number} - ${self.total}"

