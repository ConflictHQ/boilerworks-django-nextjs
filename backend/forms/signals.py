"""Form engine signals — trigger notifications on form events."""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='forms.FormSubmission')
def on_form_submission_created(sender, instance, created, **kwargs):
    """Send notifications when a new submission is created."""
    if created and instance.status == 'submitted':
        from forms.tasks import send_form_submission_notification
        send_form_submission_notification.delay(instance.pk)
