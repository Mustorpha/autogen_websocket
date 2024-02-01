from django.db import models
from django.contrib.auth import get_user_model

import uuid

User = get_user_model()

class ActiveConnection(models.Model):
    """Tracks currrent active users of autogen"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField()
    token_used = models.IntegerField(default=0, null=False, blank=False)
    connect_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    disconnect_at = models.DateTimeField(null=True, blank=True)
