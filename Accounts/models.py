from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Q

class User(AbstractUser):
    
    def __str__(self):
        return f"{self.username}"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "profile": self.profile.to_dict(),
        }
    
    @property
    def initials(self):
        a = ""
        b = ""
        if self.first_name:
            a = self.first_name[0]
        if self.last_name:
            b = self.last_name[0]
        c = a+b
        if c=="":
            c = "NA"
        return str(c)
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    dp = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"