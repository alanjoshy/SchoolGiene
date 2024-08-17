from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class SchoolUser(AbstractUser):
    
    designation = (
        ('student', 'student'),
        ('staff', 'staff'),
    )
    
    name = models.CharField(unique=True, null=True, blank=True, max_length=20)
    username = models.CharField(unique=True, null=True, blank=True, max_length=20)
    joined_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    phone = models.CharField(max_length=10)
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    password = models.CharField(max_length=100, null=True, blank=True)
    forgot_password = models.CharField(max_length=100, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photo', null=True, blank=True, default='profile.png')
    email = models.EmailField(unique=True)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    last_login_time = models.DateTimeField(default=timezone.now, null=True, blank=True)
    role = models.CharField(max_length=100, choices=designation, default='student')
    address = models.CharField(max_length=250, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    def save(self, *args, **kwargs):
        # Truncate the username (email) if it's longer than 20 characters
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username 
    
    
class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    students = models.ManyToManyField(SchoolUser, related_name='courses_enrolled', limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return self.name

    def enroll_student(self, student):
        # Enroll the student in the course
        self.students.add(student)
        
        # Enroll the student in all subjects of this course
        for subject in self.subjects.all():
            subject.students.add(student)


class Subject(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    staff_assigned = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, limit_choices_to={'role': 'staff'}, related_name='subjects_taught')
    students = models.ManyToManyField(SchoolUser, related_name='subjects_enrolled', limit_choices_to={'role': 'student'})
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    def __str__(self):
        return self.name 
    
