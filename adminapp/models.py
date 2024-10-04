from django.utils import timezone
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from datetime import timedelta


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
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username 
    
    def generate_reset_token(self):
        # Generates a token and sets its expiry (e.g., 1 hour from now)
        import uuid
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiry = timezone.now() + timedelta(hours=1)
        self.save()

    def is_reset_token_valid(self, token):
        # Checks if the token is valid (exists and hasn't expired)
        if self.reset_token == token and self.reset_token_expiry > timezone.now():
            return True
        return False

class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    students = models.ManyToManyField(SchoolUser, related_name='courses_enrolled', limit_choices_to={'role': 'student'})
    class_teacher = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, limit_choices_to={'role': 'staff'}, related_name='courses_taught', null=True)  # Temporarily allow null values
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
    

class Session(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "Fall 2024"
    start_year = models.PositiveIntegerField()  # e.g., 2024
    end_year = models.PositiveIntegerField()  # e.g., 2025
    courses = models.ManyToManyField('Course', related_name='sessions')  # Linking with courses

    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        unique_together = ('name', 'start_year', 'end_year')

    def __str__(self):
        return f"{self.name} ({self.start_year}-{self.end_year})"

    def add_course(self, course):
        """Associate a course with this session."""
        self.courses.add(course)
        
class Exam(models.Model):
    name = models.CharField(max_length=200)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='exams')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exams')
    exam_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('name', 'session', 'course', 'subject')

    def __str__(self):
        return f"{self.name} - {self.subject.name} ({self.session.name})" 
    
    
class ExamResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='exam_results')
    assignment_marks = models.FloatField(default=0)  # New field for assignment marks
    marks_obtained = models.FloatField()  # Existing field for exam marks
    max_marks = models.FloatField(default=100)  # Fixed max marks
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('exam', 'student')

    def __str__(self):
        return f"{self.student.name} - {self.exam.name} - {self.assignment_marks}/{self.max_marks} (Assignment), {self.exam_marks}/{self.max_marks} (Exam)" 
    
    
    
# model for leave 
class Leave(models.Model):
    LEAVE_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()  # Start date of the leave
    end_date = models.DateField()  # End date of the leave
    reason = models.TextField()  # Reason for leave
    status = models.CharField(max_length=20, choices=LEAVE_STATUS_CHOICES, default='pending')  # Leave status
    applied_at = models.DateTimeField(default=timezone.now)  # Timestamp when the leave was applied
    approved_at = models.DateTimeField(null=True, blank=True)  # Timestamp when the leave was approved or rejected

    class Meta:
        unique_together = ('user', 'start_date', 'end_date')
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.user.username} - {self.start_date} to {self.end_date} ({self.status})"

    @property
    def user_role(self):
        return self.user.role 
    
    
    
class Feedback(models.Model):
    # Choices for sender role
    SENDER_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
    ]
    
    # Sender of the feedback
    sender_role = models.CharField(max_length=10, choices=SENDER_CHOICES)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role__in': ['student', 'staff']})
    

    
    # Feedback details
    feedback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    # Admin's reply
    feedback_reply = models.TextField(blank=True, null=True)
    reply_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback from {self.sender.username} on {self.created_at}"
    