from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, blank=True, default="General")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('FREELANCER', 'Freelancer (Looking for Work)'),
        ('CLIENT', 'Client (Looking to Hire)'),
        ('BOTH', 'Both (Freelance & Hire)'),
    )

    EXPERIENCE_CHOICES = (
        ('ENTRY', 'Entry Level (1-2 yrs)'),
        ('INTERMEDIATE', 'Intermediate (3-5 yrs)'),
        ('EXPERT', 'Expert (5+ yrs)'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FREELANCER')
    headline = models.CharField(max_length=160, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=45.00)
    location = models.CharField(max_length=100, blank=True, default="Remote")
    phone = models.CharField(max_length=30, blank=True, default="")
    company_name = models.CharField(max_length=150, blank=True, default="")
    website = models.URLField(blank=True, default="")
    github = models.URLField(blank=True, default="")
    skills = models.ManyToManyField(Skill, blank=True, related_name='users')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='INTERMEDIATE')
    avatar_url = models.URLField(blank=True, default="")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_available_for_hire = models.BooleanField(default=True)
    job_success_score = models.PositiveIntegerField(default=100)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    @property
    def is_client(self):
        return self.role in ('CLIENT', 'BOTH')

    @property
    def is_freelancer(self):
        return self.role in ('FREELANCER', 'BOTH')

    @property
    def avatar_display(self):
        if self.avatar:
            return self.avatar.url
        if self.avatar_url:
            return self.avatar_url
        initials = (self.first_name[:1] + self.last_name[:1]) or self.username[:2]
        return f"https://ui-avatars.com/api/?name={initials}&background=6366F1&color=fff&bold=true"

    @property
    def average_rating(self):
        agg = self.received_reviews.aggregate(avg=Avg('rating'))
        if agg['avg'] is not None:
            return round(agg['avg'], 1)
        return 5.0

    @property
    def review_count(self):
        return self.received_reviews.count()

    def __str__(self):
        full = self.get_full_name()
        return f"{full} (@{self.username})" if full else self.username


class PortfolioItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    project_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tech tags")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class SavedFreelancer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_freelancers')
    freelancer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'freelancer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} saved {self.freelancer.username}"
