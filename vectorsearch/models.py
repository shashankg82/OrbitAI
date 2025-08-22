from django.db import models

class Persona(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    age = models.IntegerField()
    bio = models.TextField()
    job_role = models.CharField(max_length=100)
    hobbies = models.JSONField(default=list)  
    smoker = models.BooleanField()
    location = models.CharField(max_length=100)
    embedding = models.JSONField(null=True, blank=True) 

    def __str__(self):
        return f"{self.name} ({self.job_role})"


