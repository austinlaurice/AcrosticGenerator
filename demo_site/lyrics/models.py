from django.db import models

# Create your models here.
class Locker_en(models.Model):
    is_using = models.BooleanField(default=False)
