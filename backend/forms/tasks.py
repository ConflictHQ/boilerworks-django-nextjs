"""Celery tasks for form event notifications."""
import logging

from config.celery import app
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@app.task()
def send_form_submission_notification(submission_id):
    """Send notifications when a form is submitted."""
    from core.models import Notification
    from forms.models import FormSubmission

    submission = FormSubmission.objects.select_related('form', 'submitted_by').filter(pk=submission_id).first()
    if not submission:
        logger.warning(f'FormSubmission {submission_id} not found for notification')
        return

    form = submission.form
    config = form.notification_config.get('on_submit', {})
    if not config:
        return

    notify_list = config.get('notify', [])
    subject_template = config.get('subject_template', 'New submission: {form_name}')
    message_template = config.get('message_template', '{submitter} submitted "{form_name}" (v{version})')

    context = {
        'form_name': form.name,
        'form_slug': form.slug,
        'version': form.version,
        'submitter': submission.submitted_by.username if submission.submitted_by else 'Anonymous',
        'submission_id': str(submission.pk),
    }

    subject = subject_template.format(**context)
    message = message_template.format(**context)

    recipients = _resolve_recipients(notify_list, form, submission)
    for user in recipients:
        Notification.objects.create(
            user=user,
            subject=subject,
            message=message,
            created_by=submission.submitted_by,
            updated_by=submission.submitted_by,
        )

    logger.info(f'Sent {len(recipients)} notification(s) for submission {submission_id}')


@app.task()
def send_form_status_change_notification(submission_id, new_status):
    """Send notifications when a submission status changes."""
    from core.models import Notification
    from forms.models import FormSubmission

    submission = FormSubmission.objects.select_related('form', 'submitted_by').filter(pk=submission_id).first()
    if not submission:
        return

    form = submission.form
    config = form.notification_config.get('on_status_change', {})
    if not config:
        return

    notify_list = config.get('notify', [])
    subject_template = config.get('subject_template', 'Submission status: {status}')
    message_template = config.get('message_template', 'Your submission to "{form_name}" is now {status}.')

    context = {
        'form_name': form.name,
        'status': new_status,
        'submission_id': str(submission.pk),
    }

    subject = subject_template.format(**context)
    message = message_template.format(**context)

    recipients = _resolve_recipients(notify_list, form, submission)
    for user in recipients:
        Notification.objects.create(
            user=user,
            subject=subject,
            message=message,
            created_by=submission.submitted_by,
            updated_by=submission.submitted_by,
        )


def _resolve_recipients(notify_list, form, submission):
    """Resolve notification recipient references to User objects."""
    recipients = set()
    for ref in notify_list:
        if ref == 'form_owner' and form.created_by:
            recipients.add(form.created_by)
        elif ref == 'submitter' and submission.submitted_by:
            recipients.add(submission.submitted_by)
        elif isinstance(ref, (int, str)):
            try:
                user = User.objects.get(pk=ref)
                recipients.add(user)
            except (User.DoesNotExist, ValueError):
                pass
    return list(recipients)
