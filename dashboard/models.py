from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ShortenedURL(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    # owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    original_url = models.CharField(max_length=1000)
    short_code = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_url

