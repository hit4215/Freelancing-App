from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .models import Conversation, Message
from accounts.models import CustomUser
from jobs.models import Job

@login_required
def inbox_view(request, conversation_id=None):
    # Fetch all user conversations
    user_conversations = list(Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'messages').order_by('-updated_at'))

    for conv in user_conversations:
        conv.other_user = conv.get_other_participant(request.user)
        conv.unread_count = conv.unread_count_for(request.user)

    active_conversation = None
    chat_messages = []
    other_user = None

    if conversation_id:
        active_conversation = get_object_or_404(
            Conversation.objects.prefetch_related('participants', 'messages__sender'),
            id=conversation_id,
            participants=request.user
        )
    elif user_conversations:
        active_conversation = user_conversations[0]

    if active_conversation:
        other_user = active_conversation.get_other_participant(request.user)
        # Mark unread messages as read
        active_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        chat_messages = active_conversation.messages.select_related('sender').all()

    context = {
        'conversations': user_conversations,
        'active_conversation': active_conversation,
        'chat_messages': chat_messages,
        'other_user': other_user,
    }
    return render(request, 'messaging/inbox.html', context)



@login_required
def start_conversation_view(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)

    if target_user == request.user:
        messages.warning(request, "You cannot start a conversation with yourself.")
        return redirect('inbox')

    # Check if a conversation between these two already exists
    conv = Conversation.objects.filter(participants=request.user).filter(participants=target_user).first()

    job_id = request.GET.get('job_id')
    job = None
    if job_id:
        job = Job.objects.filter(id=job_id).first()

    if not conv:
        subject = f"Discussion with {target_user.get_full_name() or target_user.username}"
        if job:
            subject = f"Inquiry: {job.title[:60]}"
        elif request.user.is_freelancer and target_user.is_freelancer:
            subject = f"Networking: {request.user.first_name} & {target_user.first_name}"

        conv = Conversation.objects.create(
            subject=subject,
            job=job
        )
        conv.participants.add(request.user, target_user)

    return redirect('conversation_detail', conversation_id=conv.id)


@login_required
def send_message_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body
            )
            conversation.save() # update updated_at timestamp

            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                return JsonResponse({
                    'status': 'success',
                    'message_id': msg.id,
                    'body': msg.body,
                    'sender': msg.sender.username,
                    'sender_name': msg.sender.get_full_name() or msg.sender.username,
                    'sender_avatar': msg.sender.avatar_display,
                    'created_at': msg.created_at.strftime('%b %d, %H:%M'),
                    'is_me': True
                })

    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def fetch_messages_api(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    new_messages = conversation.messages.filter(id__gt=last_id).select_related('sender').order_by('created_at')

    # Mark unread
    new_messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    data = []
    for m in new_messages:
        data.append({
            'id': m.id,
            'body': m.body,
            'sender': m.sender.username,
            'sender_name': m.sender.get_full_name() or m.sender.username,
            'sender_avatar': m.sender.avatar_display,
            'created_at': m.created_at.strftime('%b %d, %H:%M'),
            'is_me': m.sender == request.user,
        })

    return JsonResponse({'status': 'success', 'messages': data})
