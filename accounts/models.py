import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    invited_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invitees'
    )

    def __str__(self):
        return self.username


class InviteToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invites_sent'
    )
    used_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invite_used'
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    @classmethod
    def create_for_user(cls, user, days=7):
        return cls.objects.create(
            created_by=user,
            expires_at=timezone.now() + timedelta(days=days)
        )

    def __str__(self):
        status = 'used' if self.is_used else 'valid'
        return f"Invite by {self.created_by.username} ({status})"
