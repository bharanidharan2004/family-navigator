from django.db import models
from django.contrib.auth.models import User

class Person(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Relationship(models.Model):
    RELATION_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person1 = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='relations_from')
    person2 = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='relations_to')
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES)

    def __str__(self):
        return f"{self.person1.name} → {self.relation_type} → {self.person2.name}"