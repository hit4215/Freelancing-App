import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Skill, PortfolioItem
from jobs.models import Category, Job, Proposal, Contract, ContractMilestone, Invoice, SavedJob, JobInvitation
from messaging.models import Conversation, Message
from reviews.models import Review
from core.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds realistic sample data for LancerPulse platform'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding LancerPulse platform data..."))

        # 1. Categories
        categories_data = [
            ("Web & Full-Stack Development", "fa-solid fa-code", "Python, Django, React, Node.js, Next.js, and modern full-stack web applications."),
            ("AI & Machine Learning", "fa-solid fa-brain", "LLMs, RAG architectures, PyTorch, LangChain, deep learning, and computer vision."),
            ("UI/UX & Product Design", "fa-solid fa-palette", "Design systems, Figma wireframes, UX research, responsive web & mobile UI."),
            ("Mobile App Engineering", "fa-solid fa-mobile-screen-button", "Flutter, React Native, Swift iOS, Kotlin Android mobile applications."),
            ("Cloud, DevOps & Cyber", "fa-solid fa-cloud", "AWS, Docker, Kubernetes, Terraform, CI/CD pipelines, and cloud security."),
            ("Data Science & Analytics", "fa-solid fa-chart-line", "Pandas, data modeling, automated ETL pipelines, SQL, and interactive dashboards."),
            ("Blockchain & Web3", "fa-solid fa-cubes", "Solidity, smart contract audits, decentralized protocols, and Web3 apps."),
            ("Content & SEO Strategy", "fa-solid fa-pen-nib", "Technical writing, API documentation, organic search growth, and copywriting."),
        ]

        cat_objs = {}
        for name, icon, desc in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'description': desc}
            )
            cat_objs[name] = cat

        # 2. Skills
        skills_data = [
            ("Python", "Backend"), ("Django", "Backend"), ("FastAPI", "Backend"),
            ("React", "Frontend"), ("Next.js", "Frontend"), ("TypeScript", "Frontend"),
            ("CSS3 & Vanilla JS", "Frontend"), ("TailwindCSS", "Frontend"),
            ("PyTorch", "AI"), ("LangChain", "AI"), ("LLM Fine-Tuning", "AI"),
            ("PostgreSQL", "Database"), ("Redis", "Database"), ("Docker", "DevOps"),
            ("Kubernetes", "DevOps"), ("AWS Cloud", "DevOps"), ("Flutter", "Mobile"),
            ("Swift iOS", "Mobile"), ("Figma", "Design"), ("UI/UX Design", "Design"),
        ]

        skill_objs = {}
        for name, category in skills_data:
            skill, _ = Skill.objects.get_or_create(name=name, defaults={'category': category})
            skill_objs[name] = skill

        # 3. Create Clients
        sarah, _ = User.objects.get_or_create(
            username="sarah_client",
            defaults={
                'email': "sarah@nexgencloud.io",
                'first_name': "Sarah",
                'last_name': "Jenkins",
                'role': "CLIENT",
                'headline': "VP of Engineering @ NexGen Cloud Labs",
                'company_name': "NexGen Cloud Labs",
                'location': "San Francisco, CA",
                'website': "https://nexgencloud.io",
                'total_spent': 24500.00,
                'avatar_url': "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
            }
        )
        sarah.set_password("password123")
        sarah.save()

        marcus, _ = User.objects.get_or_create(
            username="marcus_ventures",
            defaults={
                'email': "marcus@apexventures.co",
                'first_name': "Marcus",
                'last_name': "Vance",
                'role': "CLIENT",
                'headline': "Founding Partner @ Apex Tech Ventures",
                'company_name': "Apex Tech Ventures",
                'location': "New York, NY",
                'website': "https://apexventures.co",
                'total_spent': 38000.00,
                'avatar_url': "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150&auto=format&fit=crop&q=80",
            }
        )
        marcus.set_password("password123")
        marcus.save()

        # 4. Create Top Freelancers
        alex, _ = User.objects.get_or_create(
            username="alex_dev",
            defaults={
                'email': "alex@devcraft.io",
                'first_name': "Alex",
                'last_name': "Mercer",
                'role': "FREELANCER",
                'headline': "Lead Full-Stack Python & Django Engineer | SaaS Architect",
                'bio': "Full-stack engineer with 7+ years building enterprise Django, PostgreSQL, Redis, and modern frontend web apps. Obsessed with clean architecture, sub-100ms API response times, and bulletproof security.",
                'hourly_rate': 75.00,
                'location': "Berlin, Germany",
                'github': "https://github.com/alexmercer-dev",
                'website': "https://alexmercer.io",
                'experience_level': "EXPERT",
                'job_success_score': 99,
                'total_earned': 64200.00,
                'avatar_url': "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            }
        )
        alex.set_password("password123")
        alex.save()
        alex.skills.set([skill_objs["Python"], skill_objs["Django"], skill_objs["PostgreSQL"], skill_objs["Redis"], skill_objs["Docker"], skill_objs["React"]])

        elena, _ = User.objects.get_or_create(
            username="elena_ai",
            defaults={
                'email': "elena@aistudios.io",
                'first_name': "Elena",
                'last_name': "Rostova",
                'role': "FREELANCER",
                'headline': "Senior AI & LLM Systems Architect | PyTorch & LangChain",
                'bio': "Specializing in generative AI, Retrieval Augmented Generation (RAG), vector databases, and fine-tuning open-weights models for high-concurrency enterprise applications.",
                'hourly_rate': 95.00,
                'location': "Toronto, Canada",
                'github': "https://github.com/elena-ai-labs",
                'experience_level': "EXPERT",
                'job_success_score': 100,
                'total_earned': 82500.00,
                'avatar_url': "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
            }
        )
        elena.set_password("password123")
        elena.save()
        elena.skills.set([skill_objs["Python"], skill_objs["PyTorch"], skill_objs["LangChain"], skill_objs["LLM Fine-Tuning"], skill_objs["FastAPI"]])

        david, _ = User.objects.get_or_create(
            username="david_design",
            defaults={
                'email': "david@designcraft.io",
                'first_name': "David",
                'last_name': "Chen",
                'role': "FREELANCER",
                'headline': "Principal UI/UX & Design Systems Engineer (Figma, Clean CSS)",
                'bio': "Crafting pixel-perfect, accessible, and conversion-focused web interfaces and mobile design systems. Over 40 shipped consumer & B2B SaaS products.",
                'hourly_rate': 65.00,
                'location': "London, UK",
                'website': "https://davidchen.design",
                'experience_level': "EXPERT",
                'job_success_score': 98,
                'total_earned': 45000.00,
                'avatar_url': "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
            }
        )
        david.set_password("password123")
        david.save()
        david.skills.set([skill_objs["Figma"], skill_objs["UI/UX Design"], skill_objs["CSS3 & Vanilla JS"], skill_objs["TailwindCSS"]])

        priya, _ = User.objects.get_or_create(
            username="priya_mobile",
            defaults={
                'email': "priya@fluttercraft.org",
                'first_name': "Priya",
                'last_name': "Sharma",
                'role': "FREELANCER",
                'headline': "Lead Cross-Platform Mobile Engineer (Flutter & iOS Swift)",
                'bio': "Passionate mobile engineer delivering 60fps native performance across iOS and Android with Flutter and Swift. Experienced with offline-first sync, push notifications, and payment gateways.",
                'hourly_rate': 60.00,
                'location': "Bangalore, India",
                'github': "https://github.com/priyasharma-mobile",
                'experience_level': "INTERMEDIATE",
                'job_success_score': 99,
                'total_earned': 39000.00,
                'avatar_url': "https://images.unsplash.com/photo-1534751516642-a171edd2521d?w=150&auto=format&fit=crop&q=80",
            }
        )
        priya.set_password("password123")
        priya.save()
        priya.skills.set([skill_objs["Flutter"], skill_objs["Swift iOS"], skill_objs["TypeScript"]])

        liam, _ = User.objects.get_or_create(
            username="liam_cloud",
            defaults={
                'email': "liam@cloudforge.tech",
                'first_name': "Liam",
                'last_name': "O'Connor",
                'role': "FREELANCER",
                'headline': "Cloud Infrastructure & Site Reliability Engineer (AWS, K8s, Terraform)",
                'bio': "Specializing in zero-downtime deployments, Kubernetes clusters, infrastructure as code, automated CI/CD pipelines, and observability.",
                'hourly_rate': 85.00,
                'location': "Austin, TX",
                'experience_level': "EXPERT",
                'job_success_score': 100,
                'total_earned': 71000.00,
                'avatar_url': "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
            }
        )
        liam.set_password("password123")
        liam.save()
        liam.skills.set([skill_objs["AWS Cloud"], skill_objs["Kubernetes"], skill_objs["Docker"], skill_objs["PostgreSQL"]])

        # Portfolio Items
        PortfolioItem.objects.get_or_create(
            user=alex,
            title="HealthPulse HIPAA Medical EHR SaaS",
            defaults={
                'description': "High-security healthcare management portal with multi-tenant architecture, real-time patient queue, and automated prescription routing.",
                'project_url': "https://github.com/alexmercer-dev/healthpulse",
                'image_url': "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=400&auto=format&fit=crop&q=80",
                'tags': "Django, PostgreSQL, Redis, Docker, React"
            }
        )

        PortfolioItem.objects.get_or_create(
            user=elena,
            title="FinanceRAG - Multi-Document Financial Analyzer",
            defaults={
                'description': "Engineered an enterprise vector search and retrieval pipeline capable of synthesizing 10-K financial filings with source citations in under 2 seconds.",
                'project_url': "https://github.com/elena-ai-labs/fin-rag",
                'image_url': "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&auto=format&fit=crop&q=80",
                'tags': "PyTorch, LangChain, Milvus, FastAPI"
            }
        )

        # 5. Create Realistic Job Postings
        job1, _ = Job.objects.get_or_create(
            client=sarah,
            title="Enterprise Healthcare SaaS in Django, PostgreSQL & Redis",
            defaults={
                'category': cat_objs["Web & Full-Stack Development"],
                'description': """We are seeking a senior backend Django specialist to architect and develop our next-generation patient scheduling and diagnostic portal.

Key Deliverables:
- Implement secure, HIPAA-compliant patient management endpoints.
- Real-time notification worker using Celery and Redis.
- Comprehensive REST APIs for our Next.js frontend application.
- Automated test coverage > 85% with Pytest.

Requirements:
- Proven production experience with Django 5+ and PostgreSQL.
- Understanding of role-based permissions and token-based authentication.
- Strong communication and async update discipline.""",
                'budget_type': 'FIXED',
                'budget_min': 4500.00,
                'budget_max': 6000.00,
                'experience_level': 'EXPERT',
                'location_type': 'REMOTE',
                'status': 'OPEN',
                'deadline_days': 21,
            }
        )
        job1.skills.set([skill_objs["Python"], skill_objs["Django"], skill_objs["PostgreSQL"], skill_objs["Redis"]])

        job2, _ = Job.objects.get_or_create(
            client=marcus,
            title="Fine-Tuning LLM & RAG Chatbot Pipeline for Financial Compliance",
            defaults={
                'category': cat_objs["AI & Machine Learning"],
                'description': """Looking for an expert AI/LLM engineer to construct a robust Retrieval Augmented Generation (RAG) system integrated with Llama 3 / Mistral.

Scope:
- Ingestion pipeline for large PDF financial prospectuses and compliance filings.
- Chunking, hybrid embedding search (dense + sparse), and reranking.
- Evaluation metrics framework to guard against hallucinations.
- Lightweight FastAPI microservice ready for Docker deployment.""",
                'budget_type': 'FIXED',
                'budget_min': 3500.00,
                'budget_max': 5000.00,
                'experience_level': 'EXPERT',
                'location_type': 'REMOTE',
                'status': 'OPEN',
                'deadline_days': 14,
            }
        )
        job2.skills.set([skill_objs["Python"], skill_objs["LangChain"], skill_objs["PyTorch"], skill_objs["LLM Fine-Tuning"]])

        job3, _ = Job.objects.get_or_create(
            client=sarah,
            title="Modern Fintech Mobile App UI/UX Design System in Figma",
            defaults={
                'category': cat_objs["UI/UX & Product Design"],
                'description': """We are launching an international multi-currency wallet app and need an inspiring, eye-catching, and elegant UI/UX designer.

Deliverables:
- Complete Figma component library & design system (Dark & Light tokens).
- 25+ responsive screens for onboarding, transaction history, charts, and card management.
- Interactive clickable prototype for user testing and stakeholder pitch.""",
                'budget_type': 'HOURLY',
                'budget_min': 55.00,
                'budget_max': 75.00,
                'experience_level': 'INTERMEDIATE',
                'location_type': 'REMOTE',
                'status': 'OPEN',
                'deadline_days': 15,
            }
        )
        job3.skills.set([skill_objs["Figma"], skill_objs["UI/UX Design"], skill_objs["TailwindCSS"]])

        job4, _ = Job.objects.get_or_create(
            client=marcus,
            title="Cross-Platform Flutter E-Commerce & Delivery App with Stripe",
            defaults={
                'category': cat_objs["Mobile App Engineering"],
                'description': """We need an experienced Flutter developer to build our consumer mobile app supporting catalog browsing, real-time courier geolocation, and in-app checkout via Stripe.

Deliverables:
- Clean Bloc / Riverpod state management.
- Google Maps live tracking integration.
- Smooth animations and native feel across both iOS and Android.""",
                'budget_type': 'FIXED',
                'budget_min': 4000.00,
                'budget_max': 5500.00,
                'experience_level': 'EXPERT',
                'location_type': 'REMOTE',
                'status': 'OPEN',
                'deadline_days': 20,
            }
        )
        job4.skills.set([skill_objs["Flutter"], skill_objs["TypeScript"]])

        job5, _ = Job.objects.get_or_create(
            client=sarah,
            title="Kubernetes Multi-Region Cluster Setup & CI/CD Pipeline Automation",
            defaults={
                'category': cat_objs["Cloud, DevOps & Cyber"],
                'description': """Need a DevOps wizard to configure highly available EKS clusters on AWS with Terraform, automated GitHub Actions CI/CD, and Prometheus/Grafana alerting.""",
                'budget_type': 'FIXED',
                'budget_min': 3200.00,
                'budget_max': 4500.00,
                'experience_level': 'EXPERT',
                'location_type': 'REMOTE',
                'status': 'OPEN',
                'deadline_days': 10,
            }
        )
        job5.skills.set([skill_objs["AWS Cloud"], skill_objs["Kubernetes"], skill_objs["Docker"]])

        # 6. Proposals
        prop1, _ = Proposal.objects.get_or_create(
            job=job1,
            freelancer=alex,
            defaults={
                'bid_amount': 5200.00,
                'estimated_days': 18,
                'cover_letter': "Hi Sarah! I have built 4 production healthcare SaaS platforms in Django. I recently delivered an EHR system with full HIPAA compliance and sub-80ms queries on a 2M record PostgreSQL database. I can begin immediately and provide daily progress updates.",
                'status': 'PENDING'
            }
        )

        prop2, _ = Proposal.objects.get_or_create(
            job=job2,
            freelancer=elena,
            defaults={
                'bid_amount': 4500.00,
                'estimated_days': 12,
                'cover_letter': "Hello Marcus, my specialty is high-accuracy RAG architectures for finance and compliance. I can deliver a prototype with reranking and citation grounding within 7 days, complete with unit tests and Docker orchestration.",
                'status': 'PENDING'
            }
        )

        # 7. Completed Job, Contract & 5-Star Reviews
        comp_job, _ = Job.objects.get_or_create(
            client=sarah,
            title="Cloud Data Pipeline & Microservices Migration",
            defaults={
                'category': cat_objs["Web & Full-Stack Development"],
                'description': "Migrate monolithic backend services to asynchronous worker pipelines with Redis and PostgreSQL.",
                'budget_type': 'FIXED',
                'budget_min': 3500.00,
                'budget_max': 3500.00,
                'experience_level': 'EXPERT',
                'location_type': 'REMOTE',
                'status': 'COMPLETED',
                'deadline_days': 14,
            }
        )

        comp_prop, _ = Proposal.objects.get_or_create(
            job=comp_job,
            freelancer=alex,
            defaults={
                'bid_amount': 3500.00,
                'estimated_days': 12,
                'cover_letter': "Excited to optimize your pipeline services!",
                'status': 'ACCEPTED'
            }
        )

        comp_contract, _ = Contract.objects.get_or_create(
            job=comp_job,
            defaults={
                'proposal': comp_prop,
                'client': sarah,
                'freelancer': alex,
                'total_amount': 3500.00,
                'status': 'COMPLETED'
            }
        )

        Review.objects.get_or_create(
            contract=comp_contract,
            reviewer=sarah,
            defaults={
                'reviewee': alex,
                'rating': 5,
                'comment': "Alex was phenomenal! Delivered 3 days ahead of schedule with flawless documentation and clean test coverage. Would hire again in a heartbeat!"
            }
        )

        Review.objects.get_or_create(
            contract=comp_contract,
            reviewer=alex,
            defaults={
                'reviewee': sarah,
                'rating': 5,
                'comment': "Sarah is a dream client—crystal clear specifications, rapid feedback, and prompt milestone sign-off. Highly recommended to any freelancer."
            }
        )

        # Milestone & Invoice for completed contract
        ContractMilestone.objects.get_or_create(
            contract=comp_contract,
            order=1,
            defaults={
                'title': "Cloud Pipeline Architecture & Microservices Migration",
                'description': "Full asynchronous pipeline migration with Redis and PostgreSQL.",
                'amount': 3500.00,
                'status': 'APPROVED'
            }
        )
        Invoice.objects.get_or_create(
            invoice_number="INV-20260815-99C12A",
            defaults={
                'contract': comp_contract,
                'client': sarah,
                'freelancer': alex,
                'amount': 3500.00,
                'service_fee': 175.00,
                'total': 3500.00,
                'status': 'PAID',
                'notes': "Completed pipeline migration and async queue architecture"
            }
        )

        # 7b. Active Contract with Milestones & Escrow
        active_job, _ = Job.objects.get_or_create(
            client=sarah,
            title="Enterprise Real-Time Health Analytics & EHR System",
            defaults={
                'category': cat_objs["Web & Full-Stack Development"],
                'description': "Full-stack healthcare analytics application with HIPAA compliance, HL7/FHIR integration, and live telemetry.",
                'budget_type': 'FIXED',
                'budget_min': 5200.00,
                'budget_max': 5200.00,
                'experience_level': 'EXPERT',
                'location_type': 'REMOTE',
                'status': 'IN_PROGRESS',
                'deadline_days': 25,
            }
        )
        active_job.skills.set([skill_objs["Python"], skill_objs["Django"], skill_objs["PostgreSQL"], skill_objs["Redis"]])

        active_prop, _ = Proposal.objects.get_or_create(
            job=active_job,
            freelancer=alex,
            defaults={
                'bid_amount': 5200.00,
                'estimated_days': 20,
                'cover_letter': "I specialize in HIPAA-compliant healthcare data systems and real-time FHIR event streaming.",
                'status': 'ACCEPTED'
            }
        )

        active_contract, _ = Contract.objects.get_or_create(
            job=active_job,
            defaults={
                'proposal': active_prop,
                'client': sarah,
                'freelancer': alex,
                'total_amount': 5200.00,
                'status': 'ACTIVE'
            }
        )

        # Milestones for Active Contract:
        m1, _ = ContractMilestone.objects.get_or_create(
            contract=active_contract,
            order=1,
            defaults={
                'title': "Phase 1: Database Architecture & FHIR Protocol Core",
                'description': "Configure PostgreSQL schemas, audit logs, and HL7/FHIR event listener pipelines.",
                'amount': 1800.00,
                'status': 'APPROVED'
            }
        )

        Invoice.objects.get_or_create(
            invoice_number="INV-20260901-7A3F9B",
            defaults={
                'contract': active_contract,
                'client': sarah,
                'freelancer': alex,
                'amount': 1800.00,
                'service_fee': 90.00,
                'total': 1800.00,
                'status': 'PAID',
                'notes': "Milestone release: Phase 1 Database Architecture & FHIR Protocol Core"
            }
        )

        m2, _ = ContractMilestone.objects.get_or_create(
            contract=active_contract,
            order=2,
            defaults={
                'title': "Phase 2: React/Next.js Patient Portal & Telemetry Frontend",
                'description': "Interactive real-time patient charts with WebSocket telemetry and medical history view.",
                'amount': 2000.00,
                'status': 'SUBMITTED',
                'submission_notes': "Completed frontend UI components, responsive dashboards, and automated vitals chart streaming. Unit tests coverage at 92%.",
                'submission_url': "https://github.com/alexmercer-dev/health-portal-preview"
            }
        )

        m3, _ = ContractMilestone.objects.get_or_create(
            contract=active_contract,
            order=3,
            defaults={
                'title': "Phase 3: HIPAA Security Audit & Production Deployment",
                'description': "Conduct vulnerability scans, data encryption at rest/transit verification, and production rollout.",
                'amount': 1400.00,
                'status': 'PENDING'
            }
        )

        # 8. Saved Jobs
        SavedJob.objects.get_or_create(user=alex, job=job2)
        SavedJob.objects.get_or_create(user=alex, job=job3)
        SavedJob.objects.get_or_create(user=elena, job=job1)

        # 9. Job Invitations
        JobInvitation.objects.get_or_create(
            job=job1,
            freelancer=elena,
            defaults={
                'client': sarah,
                'message': "Hi Elena! We reviewed your AI portfolio and would love for you to submit a proposal for our Healthcare Analytics platform.",
                'status': 'PENDING'
            }
        )
        JobInvitation.objects.get_or_create(
            job=job2,
            freelancer=alex,
            defaults={
                'client': marcus,
                'message': "Hello Alex! Your distributed systems experience is a great fit for our high-accuracy financial intelligence engine.",
                'status': 'ACCEPTED'
            }
        )

        # 10. In-App Notifications
        Notification.objects.get_or_create(
            recipient=alex,
            title="Milestone Approved: $1,800.00",
            defaults={
                'actor': sarah,
                'notification_type': 'PAYMENT',
                'message': "Sarah Jenkins approved milestone 'Phase 1: Database Architecture & FHIR Protocol Core' and released $1,800.00.",
                'link': f"/contract/{active_contract.id}/",
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            recipient=sarah,
            title="Work Submitted: Phase 2",
            defaults={
                'actor': alex,
                'notification_type': 'CONTRACT',
                'message': "Alex Mercer submitted deliverables for 'Phase 2: React/Next.js Patient Portal & Telemetry Frontend'. Please review.",
                'link': f"/contract/{active_contract.id}/",
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            recipient=elena,
            title="Job Invitation from Sarah Jenkins",
            defaults={
                'actor': sarah,
                'notification_type': 'INVITATION',
                'message': "You have been invited to apply for 'AI-Driven Healthcare Patient Analytics Dashboard'.",
                'link': f"/jobs/{job1.slug}/",
                'is_read': False
            }
        )

        # 11. Direct Conversations:
        # A) Client <-> Freelancer
        conv1, _ = Conversation.objects.get_or_create(
            subject=f"Proposal Discussion: {job1.title[:50]}",
            job=job1
        )
        conv1.participants.set([sarah, alex])
        if not conv1.messages.exists():
            Message.objects.create(
                conversation=conv1,
                sender=alex,
                body="Hi Sarah! Thank you for reviewing my profile. I took a deep dive into the requirements for the Healthcare SaaS and had a quick question regarding the third-party lab integration protocol."
            )
            Message.objects.create(
                conversation=conv1,
                sender=sarah,
                body="Hello Alex! Impressive portfolio. We use HL7/FHIR standards for lab synchronization. Are you comfortable handling FHIR payloads?"
            )
            Message.objects.create(
                conversation=conv1,
                sender=alex,
                body="Yes, absolutely! I've worked extensively with python-fhir and built custom serializers for patient observation events. Looking forward to getting started!"
            )

        # B) Freelancer <-> Freelancer Networking!
        conv2, _ = Conversation.objects.get_or_create(
            subject="Peer Networking: Full-Stack & AI Co-Op Collaboration"
        )
        conv2.participants.set([alex, elena])
        if not conv2.messages.exists():
            Message.objects.create(
                conversation=conv2,
                sender=alex,
                body="Hey Elena! I saw your profile and your FinanceRAG portfolio item—really clean architecture. I frequently get clients asking for end-to-end AI applications where they need both enterprise Django backends and advanced LLM pipelines. Would you be open to teaming up on future enterprise bids?"
            )
            Message.objects.create(
                conversation=conv2,
                sender=elena,
                body="Hey Alex! That sounds fantastic! I often have clients needing full production web applications around my models, and having a reliable Django architect to partner with would let us take on larger $15k+ enterprise contracts together. Let's definitely co-bid on upcoming projects!"
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded LancerPulse with realistic sample data!"))

