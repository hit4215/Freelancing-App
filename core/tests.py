from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Skill
from jobs.models import Job, Category, Proposal, Contract, ContractMilestone, Invoice, SavedJob, JobInvitation
from messaging.models import Conversation, Message
from reviews.models import Review
from core.models import Notification

User = get_user_model()

class LancerPulseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Web Development", icon="fa-solid fa-code")
        self.skill = Skill.objects.create(name="Python", category="Backend")

        # Create Client User
        self.client_user = User.objects.create_user(
            username="tech_client",
            email="client@test.com",
            password="testpassword123",
            role="CLIENT",
            company_name="Test Ventures"
        )

        # Create Freelancer User
        self.freelancer_user = User.objects.create_user(
            username="code_freelancer",
            email="freelancer@test.com",
            password="testpassword123",
            role="FREELANCER",
            headline="Full Stack Engineer",
            hourly_rate=65.00
        )
        self.freelancer_user.skills.add(self.skill)

        # Create Freelancer Peer (for networking tests)
        self.peer_freelancer = User.objects.create_user(
            username="ai_freelancer",
            email="peer@test.com",
            password="testpassword123",
            role="FREELANCER",
            headline="AI Specialist",
            hourly_rate=80.00
        )

    def test_homepage_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LancerPulse")
        self.assertContains(response, "Explore By Category")

    def test_job_list_loads(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Explore Available Projects")

    def test_freelancers_directory_loads(self):
        response = self.client.get(reverse('freelancers'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "code_freelancer")
        self.assertContains(response, "Full Stack Engineer")

    def test_post_job_flow(self):
        self.client.login(username="tech_client", password="testpassword123")
        response = self.client.post(reverse('create_job'), {
            'title': 'Build a Modern Django Platform',
            'category': self.category.id,
            'description': 'Need a scalable Django system built with responsive styling.',
            'budget_type': 'FIXED',
            'budget_min': 2000,
            'budget_max': 3000,
            'experience_level': 'EXPERT',
            'location_type': 'REMOTE',
            'deadline_days': 14,
            'skills': [self.skill.id]
        })
        self.assertEqual(Job.objects.count(), 1)
        job = Job.objects.first()
        self.assertEqual(job.client, self.client_user)
        self.assertRedirects(response, reverse('job_detail', kwargs={'slug': job.slug}))

    def test_submit_proposal_and_conversation_creation(self):
        job = Job.objects.create(
            client=self.client_user,
            title="Django App Dev",
            category=self.category,
            description="Build Django app",
            budget_type="FIXED",
            budget_min=1500,
            budget_max=2000,
            experience_level="EXPERT",
            location_type="REMOTE",
            deadline_days=10
        )

        # Login as Freelancer
        self.client.login(username="code_freelancer", password="testpassword123")
        response = self.client.post(reverse('submit_proposal', kwargs={'slug': job.slug}), {
            'bid_amount': 1800,
            'estimated_days': 8,
            'cover_letter': 'I have built over 20 Django applications and can complete this in 8 days.'
        })
        self.assertEqual(Proposal.objects.count(), 1)
        proposal = Proposal.objects.first()
        self.assertEqual(proposal.bid_amount, 1800)
        self.assertEqual(proposal.freelancer, self.freelancer_user)

        # Check that conversation was automatically initialized between freelancer and client
        conv = Conversation.objects.filter(participants=self.client_user).filter(participants=self.freelancer_user).first()
        self.assertIsNotNone(conv)
        self.assertTrue(conv.messages.exists())

    def test_accept_proposal_and_complete_contract(self):
        job = Job.objects.create(
            client=self.client_user,
            title="Django App Dev",
            category=self.category,
            description="Build Django app",
            budget_type="FIXED",
            budget_min=1500,
            budget_max=2000,
            experience_level="EXPERT",
            location_type="REMOTE",
            deadline_days=10
        )
        proposal = Proposal.objects.create(
            job=job,
            freelancer=self.freelancer_user,
            bid_amount=1700,
            estimated_days=7,
            cover_letter='Fast delivery.'
        )

        # Login as Client to accept
        self.client.login(username="tech_client", password="testpassword123")
        accept_resp = self.client.get(reverse('accept_proposal', kwargs={'proposal_id': proposal.id}))
        self.assertRedirects(accept_resp, reverse('job_detail', kwargs={'slug': job.slug}))

        # Verify contract created and job status changed
        job.refresh_from_db()
        self.assertEqual(job.status, 'IN_PROGRESS')
        contract = Contract.objects.filter(job=job).first()
        self.assertIsNotNone(contract)
        self.assertEqual(contract.status, 'ACTIVE')
        self.assertEqual(contract.total_amount, 1700)

        # Complete contract
        complete_resp = self.client.post(reverse('complete_contract', kwargs={'contract_id': contract.id}))
        contract.refresh_from_db()
        self.assertEqual(contract.status, 'COMPLETED')
        self.assertEqual(contract.job.status, 'COMPLETED')
        self.assertRedirects(complete_resp, reverse('create_review', kwargs={'contract_id': contract.id}))

    def test_freelancer_to_freelancer_networking(self):
        """Verify peer-to-peer networking between freelancers"""
        self.client.login(username="code_freelancer", password="testpassword123")
        start_resp = self.client.get(reverse('start_conversation', kwargs={'user_id': self.peer_freelancer.id}))
        
        # Verify conversation created between the two freelancers
        conv = Conversation.objects.filter(participants=self.freelancer_user).filter(participants=self.peer_freelancer).first()
        self.assertIsNotNone(conv)
        self.assertRedirects(start_resp, reverse('conversation_detail', kwargs={'conversation_id': conv.id}))

        # Send a networking message
        send_resp = self.client.post(reverse('send_message', kwargs={'conversation_id': conv.id}), {
            'body': 'Hey, want to partner up on an AI + Django enterprise contract?'
        })
        self.assertEqual(conv.messages.count(), 1)
        self.assertEqual(conv.messages.first().body, 'Hey, want to partner up on an AI + Django enterprise contract?')

    def test_milestone_escrow_workflow_and_invoices(self):
        """Verify milestone creation, submission, revision, approval, and invoice generation"""
        job = Job.objects.create(
            client=self.client_user,
            category=self.category,
            title='Real-Time FinTech Engine',
            description='Build low-latency FinTech API.',
            budget_type='FIXED',
            budget_min=2000,
            budget_max=2000,
            experience_level='EXPERT',
            location_type='REMOTE',
            status='IN_PROGRESS',
            deadline_days=14
        )
        proposal = Proposal.objects.create(
            job=job,
            freelancer=self.freelancer_user,
            bid_amount=2000,
            estimated_days=10,
            cover_letter='FinTech specialist.',
            status='ACCEPTED'
        )
        contract = Contract.objects.create(
            job=job,
            proposal=proposal,
            client=self.client_user,
            freelancer=self.freelancer_user,
            total_amount=2000,
            status='ACTIVE'
        )

        # 1. Client adds milestone
        self.client.login(username="tech_client", password="testpassword123")
        add_resp = self.client.post(reverse('add_milestone', kwargs={'contract_id': contract.id}), {
            'title': 'Phase 1: Trading Engine Core',
            'description': 'Implement limit order book and matcher.',
            'amount': 1000.00,
            'order': 1,
        })
        self.assertRedirects(add_resp, reverse('contract_detail', kwargs={'contract_id': contract.id}))
        milestone = contract.milestones.first()
        self.assertIsNotNone(milestone)
        self.assertEqual(milestone.status, 'PENDING')
        self.assertEqual(float(milestone.amount), 1000.00)

        # 2. Freelancer submits deliverables
        self.client.login(username="code_freelancer", password="testpassword123")
        submit_resp = self.client.post(reverse('submit_milestone', kwargs={'milestone_id': milestone.id}), {
            'submission_notes': 'Order book implemented with 10k ops/sec benchmark.',
            'submission_url': 'https://github.com/freelancer/fintech-preview'
        })
        self.assertRedirects(submit_resp, reverse('contract_detail', kwargs={'contract_id': contract.id}))
        milestone.refresh_from_db()
        self.assertEqual(milestone.status, 'SUBMITTED')
        self.assertIn('10k ops/sec', milestone.submission_notes)

        # Verify Client received notification
        notif = Notification.objects.filter(recipient=self.client_user, notification_type='CONTRACT').first()
        self.assertIsNotNone(notif)
        self.assertIn('Work Submitted', notif.title)

        # 3. Client requests revision
        self.client.login(username="tech_client", password="testpassword123")
        rev_resp = self.client.post(reverse('request_revision', kwargs={'milestone_id': milestone.id}), {
            'revision_notes': 'Please add latency stress tests under 100 concurrent connections.'
        })
        milestone.refresh_from_db()
        self.assertEqual(milestone.status, 'REVISION_REQUESTED')
        self.assertIn('latency stress tests', milestone.submission_notes)

        # 4. Freelancer re-submits
        self.client.login(username="code_freelancer", password="testpassword123")
        self.client.post(reverse('submit_milestone', kwargs={'milestone_id': milestone.id}), {
            'submission_notes': 'Added concurrency stress tests; all 100 concurrent tests passed under 5ms.',
            'submission_url': 'https://github.com/freelancer/fintech-preview'
        })
        milestone.refresh_from_db()
        self.assertEqual(milestone.status, 'SUBMITTED')

        # 5. Client approves milestone & releases escrow
        self.client.login(username="tech_client", password="testpassword123")
        app_resp = self.client.post(reverse('approve_milestone', kwargs={'milestone_id': milestone.id}))
        milestone.refresh_from_db()
        self.assertEqual(milestone.status, 'APPROVED')
        self.assertIsNotNone(milestone.approved_at)

        # Verify invoice auto-generated
        invoice = Invoice.objects.filter(contract=contract).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.status, 'PAID')
        self.assertEqual(float(invoice.total), 1000.00)
        self.assertEqual(float(invoice.service_fee), 50.00)

        # Verify financials updated
        self.freelancer_user.refresh_from_db()
        self.client_user.refresh_from_db()
        self.assertEqual(float(self.freelancer_user.total_earned), 1000.00)
        self.assertEqual(float(self.client_user.total_spent), 1000.00)

    def test_invoice_detail_security(self):
        """Verify only contract participants or staff can view digital invoices"""
        job = Job.objects.create(
            client=self.client_user,
            category=self.category,
            title='Invoice Security Test Job',
            description='Test.',
            budget_type='FIXED',
            budget_min=1000,
            budget_max=1000,
            deadline_days=5
        )
        proposal = Proposal.objects.create(
            job=job, freelancer=self.freelancer_user, bid_amount=1000, estimated_days=5, cover_letter='Test'
        )
        contract = Contract.objects.create(
            job=job, proposal=proposal, client=self.client_user, freelancer=self.freelancer_user, total_amount=1000
        )
        invoice = Invoice.objects.create(
            invoice_number='INV-TEST-001',
            contract=contract,
            client=self.client_user,
            freelancer=self.freelancer_user,
            amount=1000,
            service_fee=50,
            total=1000
        )

        # Authorized client can view
        self.client.login(username="tech_client", password="testpassword123")
        resp = self.client.get(reverse('invoice_detail', kwargs={'invoice_id': invoice.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'INV-TEST-001')

        # Authorized freelancer can view
        self.client.login(username="code_freelancer", password="testpassword123")
        resp2 = self.client.get(reverse('invoice_detail', kwargs={'invoice_id': invoice.id}))
        self.assertEqual(resp2.status_code, 200)

        # Unauthorized third-party user cannot view
        self.client.login(username="ai_freelancer", password="testpassword123")
        resp3 = self.client.get(reverse('invoice_detail', kwargs={'invoice_id': invoice.id}))
        self.assertRedirects(resp3, reverse('dashboard'))

    def test_saved_jobs_bookmarking(self):
        """Verify bookmarking and removing saved jobs"""
        job = Job.objects.create(
            client=self.client_user,
            category=self.category,
            title='Bookmarkable AI Project',
            description='Test bookmarking.',
            budget_type='FIXED',
            budget_min=3000,
            budget_max=3000,
            deadline_days=7
        )

        self.client.login(username="code_freelancer", password="testpassword123")
        
        # Toggle save (add)
        save_resp = self.client.post(reverse('toggle_save_job', kwargs={'slug': job.slug}))
        self.assertTrue(SavedJob.objects.filter(user=self.freelancer_user, job=job).exists())

        # Toggle save again (remove)
        remove_resp = self.client.post(reverse('toggle_save_job', kwargs={'slug': job.slug}))
        self.assertFalse(SavedJob.objects.filter(user=self.freelancer_user, job=job).exists())

    def test_job_invitations_lifecycle(self):
        """Verify client inviting freelancer to an open job and freelancer responding"""
        job = Job.objects.create(
            client=self.client_user,
            category=self.category,
            title='Invite-Only Cloud Migration',
            description='Test inviting talent.',
            budget_type='FIXED',
            budget_min=4000,
            budget_max=4000,
            status='OPEN',
            deadline_days=15
        )

        # Client sends invitation
        self.client.login(username="tech_client", password="testpassword123")
        invite_resp = self.client.post(reverse('invite_freelancer', kwargs={'freelancer_id': self.freelancer_user.id}), {
            'job': job.id,
            'message': 'We would love to invite you to bid on our cloud migration project.'
        })
        self.assertRedirects(invite_resp, reverse('profile', kwargs={'username': self.freelancer_user.username}))
        
        invitation = JobInvitation.objects.filter(job=job, freelancer=self.freelancer_user).first()
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.status, 'PENDING')

        # Freelancer receives notification
        notif = Notification.objects.filter(recipient=self.freelancer_user, notification_type='INVITATION').first()
        self.assertIsNotNone(notif)
        self.assertIn('Job Invitation', notif.title)

        # Freelancer accepts invitation
        self.client.login(username="code_freelancer", password="testpassword123")
        accept_resp = self.client.get(reverse('respond_invitation', kwargs={'invitation_id': invitation.id, 'action': 'accept'}))
        self.assertRedirects(accept_resp, reverse('job_detail', kwargs={'slug': job.slug}))
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'ACCEPTED')

    def test_notification_center_and_mark_read(self):
        """Verify notification listing, filtering, and mark read actions"""
        notif1 = Notification.objects.create(
            recipient=self.freelancer_user,
            title='Notification 1',
            message='Message 1',
            link='/dashboard/',
            is_read=False
        )
        notif2 = Notification.objects.create(
            recipient=self.freelancer_user,
            title='Notification 2',
            message='Message 2',
            is_read=False
        )

        self.client.login(username="code_freelancer", password="testpassword123")

        # View notification center
        resp = self.client.get(reverse('notifications_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['unread_count'], 2)

        # Mark individual notification read and follow link
        mark_resp = self.client.get(reverse('mark_notification_read', kwargs={'notification_id': notif1.id}))
        notif1.refresh_from_db()
        self.assertTrue(notif1.is_read)
        self.assertRedirects(mark_resp, '/dashboard/')

        # Mark all read
        self.client.post(reverse('mark_all_notifications_read'))
        notif2.refresh_from_db()
        self.assertTrue(notif2.is_read)

    def test_update_job_status_view(self):
        """Verify client can update project status and unauthorized users are blocked"""
        job = Job.objects.create(
            client=self.client_user,
            title='Autonomous Trading Bot',
            category=self.category,
            description='Build automated crypto trading agent.',
            budget_type='FIXED',
            budget_min=1500,
            budget_max=3000,
            status='OPEN'
        )

        # 1. Non-client attempts status update -> blocked
        self.client.login(username="code_freelancer", password="testpassword123")
        unauth_resp = self.client.post(reverse('update_job_status', kwargs={'slug': job.slug}), {
            'status': 'CLOSED'
        })
        self.assertRedirects(unauth_resp, reverse('job_detail', kwargs={'slug': job.slug}))
        job.refresh_from_db()
        self.assertEqual(job.status, 'OPEN')

        # 2. Client updates status to IN_PROGRESS
        self.client.login(username="tech_client", password="testpassword123")
        resp1 = self.client.post(reverse('update_job_status', kwargs={'slug': job.slug}), {
            'status': 'IN_PROGRESS'
        })
        self.assertRedirects(resp1, reverse('job_detail', kwargs={'slug': job.slug}))
        job.refresh_from_db()
        self.assertEqual(job.status, 'IN_PROGRESS')

        # 3. Client updates status to COMPLETED
        resp2 = self.client.post(reverse('update_job_status', kwargs={'slug': job.slug}), {
            'status': 'COMPLETED'
        })
        self.assertRedirects(resp2, reverse('job_detail', kwargs={'slug': job.slug}))
        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')

        # 4. Client updates status to CLOSED
        resp3 = self.client.post(reverse('update_job_status', kwargs={'slug': job.slug}), {
            'status': 'CLOSED'
        })
        job.refresh_from_db()
        self.assertEqual(job.status, 'CLOSED')

    def test_proposal_blocked_when_project_not_open(self):
        """Verify freelancers cannot submit proposals to non-open projects"""
        job = Job.objects.create(
            client=self.client_user,
            title='Closed Mobile Application',
            category=self.category,
            description='Project already closed.',
            budget_type='FIXED',
            budget_min=500,
            budget_max=1000,
            status='CLOSED'
        )

        self.client.login(username="code_freelancer", password="testpassword123")
        resp = self.client.post(reverse('submit_proposal', kwargs={'slug': job.slug}), {
            'bid_amount': 750,
            'estimated_days': 5,
            'cover_letter': 'Trying to bid on closed project.'
        })
        self.assertRedirects(resp, reverse('job_detail', kwargs={'slug': job.slug}))
        self.assertEqual(Proposal.objects.filter(job=job).count(), 0)

    def test_job_list_status_filter(self):
        """Verify marketplace filters by project status"""
        job_open = Job.objects.create(
            client=self.client_user,
            title='Active Open Project',
            category=self.category,
            description='Open description',
            status='OPEN'
        )
        job_progress = Job.objects.create(
            client=self.client_user,
            title='Ongoing Project',
            category=self.category,
            description='Progress description',
            status='IN_PROGRESS'
        )

        # Default query returns open jobs
        resp_default = self.client.get(reverse('job_list'))
        self.assertEqual(resp_default.status_code, 200)
        jobs_in_page = [j.id for j in resp_default.context['page_obj']]
        self.assertIn(job_open.id, jobs_in_page)
        self.assertNotIn(job_progress.id, jobs_in_page)

        # Filter for IN_PROGRESS
        resp_progress = self.client.get(reverse('job_list'), {'status': 'IN_PROGRESS'})
        jobs_progress_page = [j.id for j in resp_progress.context['page_obj']]
        self.assertIn(job_progress.id, jobs_progress_page)
        self.assertNotIn(job_open.id, jobs_progress_page)

        # Filter for ALL
        resp_all = self.client.get(reverse('job_list'), {'status': 'ALL'})
        jobs_all_page = [j.id for j in resp_all.context['page_obj']]
        self.assertIn(job_open.id, jobs_all_page)
        self.assertIn(job_progress.id, jobs_all_page)


