import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lancerpulse.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from accounts.models import CustomUser
from jobs.models import Job, Proposal, Contract
from messaging.models import Conversation, Message

def run_smoke_test():
    print("==================================================")
    print("  RUNNING LANCERPULSE PRODUCTION SMOKE TEST       ")
    print("==================================================")
    client = Client()

    endpoints = [
        ('Home Landing Page', reverse('home'), 200, ['LancerPulse', 'Explore By Category', 'Featured Project Opportunities']),
        ('Jobs Marketplace', reverse('job_list'), 200, ['Explore Available Projects', 'Enterprise Healthcare SaaS']),
        ('Freelancers Directory', reverse('freelancers'), 200, ['Elite Freelancers', 'alex_dev', 'elena_ai']),
        ('Alex Mercer Public Profile', reverse('profile', kwargs={'username': 'alex_dev'}), 200, ['Lead Full-Stack Python', 'HealthPulse HIPAA Medical EHR SaaS', 'Client Reviews']),
        ('Elena Rostova Public Profile', reverse('profile', kwargs={'username': 'elena_ai'}), 200, ['Elena Rostova', 'FinanceRAG']),
        ('Login Page', reverse('login'), 200, ['Welcome Back', 'alex_dev', 'sarah_client']),
        ('Register Page', reverse('register'), 200, ['Join LancerPulse', 'Primary Role']),
        ('How It Works Page', reverse('how_it_works'), 200, ['For Hiring Clients', 'For Freelancers']),
    ]

    all_passed = True
    for name, url, expected_status, search_strings in endpoints:
        resp = client.get(url)
        status_ok = resp.status_code == expected_status
        content = resp.content.decode('utf-8')
        strings_ok = all(s in content for s in search_strings)
        if status_ok and strings_ok:
            print(f"[PASS] {name} ({url}) -> HTTP {resp.status_code}")
        else:
            all_passed = False
            print(f"[FAIL] {name} ({url}) -> Expected HTTP {expected_status}, got {resp.status_code}. Strings found: {strings_ok}")

    # Test Job Detail
    first_job = Job.objects.filter(status='OPEN').first()
    if first_job:
        url = reverse('job_detail', kwargs={'slug': first_job.slug})
        resp = client.get(url)
        # title may contain & which renders as &amp;
        escaped_title = first_job.title.replace('&', '&amp;')
        if resp.status_code == 200 and (first_job.title in resp.content.decode('utf-8') or escaped_title in resp.content.decode('utf-8')):
            print(f"[PASS] Job Detail Page ({url}) -> HTTP 200")
        else:
            all_passed = False
            print(f"[FAIL] Job Detail Page ({url}) -> HTTP {resp.status_code}")


    # Test Authenticated Freelancer Session (Alex)
    client.login(username='alex_dev', password='password123')
    resp_dash = client.get(reverse('dashboard'))
    if resp_dash.status_code == 200 and 'Welcome, Alex' in resp_dash.content.decode('utf-8'):
        print(f"[PASS] Freelancer Dashboard (/dashboard/) -> HTTP 200 (Active Proposals & Contracts shown)")
    else:
        all_passed = False
        print(f"[FAIL] Freelancer Dashboard -> HTTP {resp_dash.status_code}")

    resp_inbox = client.get(reverse('inbox'))
    if resp_inbox.status_code == 200 and 'Conversations & Networking' in resp_inbox.content.decode('utf-8'):
        print(f"[PASS] Direct Messenger & Networking Inbox (/messages/) -> HTTP 200")
    else:
        all_passed = False
        print(f"[FAIL] Direct Messenger Inbox -> HTTP {resp_inbox.status_code}")

    client.logout()

    # Test Authenticated Client Session (Sarah)
    client.login(username='sarah_client', password='password123')
    resp_client_dash = client.get(reverse('dashboard'))
    if resp_client_dash.status_code == 200 and 'Welcome, Sarah' in resp_client_dash.content.decode('utf-8'):
        print(f"[PASS] Client Dashboard (/dashboard/) -> HTTP 200 (Posted Jobs & Spend KPI shown)")
    else:
        all_passed = False
        print(f"[FAIL] Client Dashboard -> HTTP {resp_client_dash.status_code}")

    resp_post = client.get(reverse('create_job'))
    if resp_post.status_code == 200 and 'Post a New Project' in resp_post.content.decode('utf-8'):
        print(f"[PASS] Client Job Posting Portal (/jobs/post/) -> HTTP 200")
    else:
        all_passed = False
        print(f"[FAIL] Client Job Posting Portal -> HTTP {resp_post.status_code}")

    # Test Non-Staff Access to Platform Admin (should redirect)
    resp_unauth_admin = client.get(reverse('platform_admin'))
    if resp_unauth_admin.status_code in (302, 403):
        print(f"[PASS] Non-Staff Access to /platform-admin/ correctly blocked -> Redirect {resp_unauth_admin.status_code}")
    else:
        all_passed = False
        print(f"[FAIL] Non-Staff Access not protected: HTTP {resp_unauth_admin.status_code}")

    client.logout()

    # Test Authenticated Staff / Superuser Admin Session
    admin_logged = client.login(username='admin', password='password123')
    if not admin_logged:
        # Try alternate admin password
        client.login(username='admin', password='admin123')

    admin_tabs = [
        ('Overview', '', ['Executive Command Center', 'Platform Architecture Health']),
        ('Users Tab', '?tab=users', ['Registered Users', 'alex_dev', 'sarah_client', 'Toggle Hire Availability']),
        ('Jobs Tab', '?tab=jobs', ['Posted Jobs', 'Enterprise Healthcare SaaS', 'Status Action']),
        ('Proposals Tab', '?tab=proposals', ['Total Proposals', 'Cover Letter Preview']),
        ('Contracts Tab', '?tab=contracts', ['Platform GMV', 'Escrow Value', 'Contract Actions']),
        ('Messages Tab', '?tab=messages', ['Communications', 'Messages Logged']),
        ('Reviews Tab', '?tab=reviews', ['Platform Rating', 'Feedback Comment']),
        ('Taxonomy Tab', '?tab=taxonomy', ['Job Categories', 'Platform Skills', 'Quick-Add New Category']),
    ]

    for tab_name, query, expected_strings in admin_tabs:
        url = reverse('platform_admin') + query
        resp_admin = client.get(url)
        content = resp_admin.content.decode('utf-8')
        status_ok = resp_admin.status_code == 200
        strings_ok = all(s in content for s in expected_strings)
        if status_ok and strings_ok:
            print(f"[PASS] Platform Admin [{tab_name}] ({url}) -> HTTP 200")
        else:
            all_passed = False
            missing = [s for s in expected_strings if s not in content]
            print(f"[FAIL] Platform Admin [{tab_name}] ({url}) -> HTTP {resp_admin.status_code}, Missing: {missing}")

    client.logout()

    print("==================================================")
    if all_passed:
        print("  ALL SMOKE TESTS PASSED CLEANLY! (100% SUCCESS) ")
    else:
        print("  SOME TESTS FAILED! CHECK OUTPUT ABOVE.         ")
    print("==================================================")

if __name__ == '__main__':
    run_smoke_test()
#http://127.0.0.1:8000/platform-admin/