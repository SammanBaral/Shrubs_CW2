from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, render, redirect
from item.models import Item
from .forms import ConversationMessageForm
from django.core.exceptions import ObjectDoesNotExist

from .models import Chatting

from core.models import AuditLog
import re
from django.core.exceptions import SuspiciousOperation


def sanitize_backend_input(value):
    value = re.sub(r'<script.*?>.*?</script>', '', value, flags=re.IGNORECASE)
    value = re.sub(r'(\$ne|\$eq|\$gt|\$lt|\$regex|\{|\})', '', value, flags=re.IGNORECASE)
    value = re.sub(r'alert\s*\(', '', value, flags=re.IGNORECASE)
    return value

def validate_backend_input(value):
    if re.search(r'script|<|>|alert|\$ne|\{|\}', value, re.IGNORECASE):
        raise SuspiciousOperation('Security error: Malicious input detected.')
    return value

@login_required
def new_conversation (request, item_pk):
    item = get_object_or_404(Item, pk=item_pk)

    if item.created_by == request.user:
        return redirect('dashboard:dashboard')
    
    conversations = Chatting.objects.filter(item=item).filter(members__in=[request.user.id])

    if conversations:
        return redirect('chatting:detail', pk=conversations.first().id)

    if request.method=='POST':
        form = ConversationMessageForm(request.POST)

        if form.is_valid():
            # Sanitize and validate all fields properly
            cleaned = form.cleaned_data.copy()
            for key in cleaned:
                cleaned[key] = sanitize_backend_input(str(cleaned[key]))
                validate_backend_input(cleaned[key])
            conversation = Chatting.objects.create(item=item)
            conversation.members.add(request.user)
            conversation.members.add(item.created_by)
            conversation.save()

            conversation_message = form.save(commit=False)
            conversation_message.conversation=conversation
            conversation_message.created_by = request.user
            conversation_message.content = cleaned.get('content', conversation_message.content)
            conversation_message.save()

            # Audit log for new conversation
            AuditLog.objects.create(
                user=request.user,
                user_role='admin' if request.user.is_superuser else 'customer',
                action='CREATE_CONVERSATION',
                entity='Chatting',
                entity_id=str(conversation.id),
                old_value=None,
                new_value={'item': item_pk, 'members': [request.user.id, item.created_by.id]},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )
            AuditLog.objects.create(
                user=request.user,
                user_role='admin' if request.user.is_superuser else 'customer',
                action='SEND_MESSAGE',
                entity='ConversationMessage',
                entity_id=str(conversation_message.id),
                old_value=None,
                new_value={'content': conversation_message.content},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            return redirect('item:detail', pk=item_pk)
    else:
        form = ConversationMessageForm()

    return render(request, 'chatting/new.html',{
        'form':form
    })

@login_required

def inbox(request):
    conversations = Chatting.objects.filter(members__in=[request.user.id])
    return render(request, 'chatting/inbox.html', {
        'conversations': conversations,
      
    })






@login_required
def detail(request, pk):
    conversation = Chatting.objects.filter(members__in=[request.user.id]).get(pk=pk)
    messages = Chatting.objects.filter(members__in=[request.user.id])

      # Initialize seller information to None
    seller_username = None
    seller_image_url = None
    convo_user=None

    # Iterate through all conversations and messages
    for convo in messages:
        print(convo)

        for message in convo.messages.all():
            print(message)
            print(message.created_by)

            # Check if the message is from the seller and not the current user
            if message.created_by != request.user:
                convo_user=message.created_by.id
                seller_username = message.created_by.username

                try:
                    seller_image_url = message.created_by.selleraccount.image.url
                except ObjectDoesNotExist:
                    seller_image_url= message.created_by.userprofile.photo.url
                break  # Exit the loop once seller information is found
    
    print(convo_user)
    if request.method == 'POST':
        form=ConversationMessageForm(request.POST)

        if form.is_valid():
            # Sanitize and validate all fields
            cleaned = form.cleaned_data.copy()
            for key in cleaned:
                cleaned[key] = sanitize_backend_input(str(cleaned[key]))
                validate_backend_input(cleaned[key])
            conversation_message = form.save(commit=False)
            conversation_message.conversation = conversation
            conversation_message.created_by = request.user
            conversation_message.content = cleaned.get('content', conversation_message.content)
            conversation_message.save()

            conversation.save()

            # Audit log for sending message
            AuditLog.objects.create(
                user=request.user,
                user_role='admin' if request.user.is_superuser else 'customer',
                action='SEND_MESSAGE',
                entity='ConversationMessage',
                entity_id=str(conversation_message.id),
                old_value=None,
                new_value={'content': conversation_message.content},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            return redirect('chatting:detail', pk=pk)
    else:
        form = ConversationMessageForm()

    return render(request, 'chatting/messages.html',{
        'conversation': conversation,
        'form': form,
        'seller_username': seller_username,
        'seller_image_url': seller_image_url,
        'convo_user':convo_user
    })
# Create your views here.
