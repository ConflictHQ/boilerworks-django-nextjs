"""Celery tasks for workflow transition actions."""
import logging

import requests
from config.celery import app
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@app.task()
def execute_workflow_action(instance_id, action, from_state, to_state, user_id=None):
    """Execute a single workflow action after a state transition."""
    from workflows.models import WorkflowInstance

    instance = WorkflowInstance.objects.select_related('workflow').filter(pk=instance_id).first()
    if not instance:
        logger.warning(f'WorkflowInstance {instance_id} not found')
        return

    user = User.objects.filter(pk=user_id).first() if user_id else None
    action_type = action.get('type', '')

    try:
        match action_type:
            case 'notify_user':
                _action_notify_user(instance, action, from_state, to_state, user)
            case 'send_email':
                _action_send_email(instance, action, from_state, to_state, user)
            case 'call_webhook':
                _action_call_webhook(instance, action, from_state, to_state, user)
            case 'update_field':
                _action_update_field(instance, action)
            case 'create_notification':
                _action_create_notification(instance, action, from_state, to_state, user)
            case _:
                logger.warning(f'Unknown action type: {action_type}')
    except Exception as e:
        logger.error(f'Workflow action {action_type} failed: {e}')


def _action_notify_user(instance, action, from_state, to_state, user):
    """Send an in-app notification."""
    from core.models import Notification

    # Resolve recipient
    notify_ref = action.get('user', 'form_owner')
    recipients = _resolve_recipients(notify_ref, instance, user)

    subject = action.get('subject', f'Workflow: {instance.workflow.name}')
    message = action.get('message', f'State changed from {from_state} to {to_state}')

    for recipient in recipients:
        Notification.objects.create(
            user=recipient,
            subject=subject,
            message=message,
            created_by=user,
            updated_by=user,
        )


def _action_send_email(instance, action, from_state, to_state, user):
    """Send an email notification."""
    from django.core.mail import send_mail

    recipients = _resolve_recipients(action.get('to', 'form_owner'), instance, user)
    emails = [r.email for r in recipients if r.email]

    if emails:
        send_mail(
            subject=action.get('subject', f'Workflow: {instance.workflow.name}'),
            message=action.get('message', f'State: {from_state} → {to_state}'),
            from_email=None,
            recipient_list=emails,
            fail_silently=True,
        )


def _action_call_webhook(instance, action, from_state, to_state, user):
    """Call an external webhook."""
    url = action.get('url')
    if not url:
        return

    payload = {
        'workflow': instance.workflow.name,
        'instance_id': instance.pk,
        'object_id': instance.object_id,
        'from_state': from_state,
        'to_state': to_state,
        'user': user.username if user else None,
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.warning(f'Webhook call failed: {e}')


def _action_update_field(instance, action):
    """Update a field on the tracked object."""
    field = action.get('field')
    value = action.get('value')
    if not field:
        return

    obj = instance.content_object
    if obj and hasattr(obj, field):
        setattr(obj, field, value)
        obj.save(update_fields=[field])


def _action_create_notification(instance, action, from_state, to_state, user):
    """Alias for notify_user with more explicit naming."""
    _action_notify_user(instance, action, from_state, to_state, user)


def _resolve_recipients(ref, instance, user):
    """Resolve a recipient reference to User objects."""
    recipients = set()

    if ref == 'current_user' and user:
        recipients.add(user)
    elif ref == 'form_owner':
        obj = instance.content_object
        if obj and hasattr(obj, 'created_by') and obj.created_by:
            recipients.add(obj.created_by)
    elif ref == 'submitter':
        obj = instance.content_object
        if obj and hasattr(obj, 'submitted_by') and obj.submitted_by:
            recipients.add(obj.submitted_by)
    elif isinstance(ref, (int, str)):
        try:
            recipients.add(User.objects.get(pk=ref))
        except (User.DoesNotExist, ValueError):
            pass

    return list(recipients)
