from django.db import models
from adminapp.models import  SchoolUser , Subject , Exam 
from django.utils import timezone
from django.db.models import Count, Q

class Attendance(models.Model):
    student = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.BooleanField(default=False)  # True for Present, False for Absent

    class Meta:
        unique_together = ('student', 'subject', 'date')

    def __str__(self):
        return f"{self.student.name} - {self.subject.name} - {self.date}"

def get_attendance_statistics(student):
    total_days = Attendance.objects.filter(student=student).count()
    total_present = Attendance.objects.filter(student=student, status=True).count()
    total_absent = Attendance.objects.filter(student=student, status=False).count()
    total_classes = Subject.objects.filter(students=student).aggregate(
        total_classes=Count('attendance', distinct=True)
    )['total_classes']
    
    return {
        "total_days": total_days,
        "total_present": total_present,
        "total_absent": total_absent,
        "total_classes": total_classes,
        "attendance_percentage": (total_present / total_days * 100) if total_days > 0 else 0
    }





