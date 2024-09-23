from django.db import models
from adminapp.models import SchoolUser,ExamResult
# Create your models here. 
class Fee(models.Model):
    student = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    scholarship_reduction = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)  
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def apply_scholarship(self, student):
        exam_results = ExamResult.objects.filter(student=student)
        for result in exam_results:
            if result.qualifies_for_scholarship():
                self.scholarship_reduction = self.amount_due * 0.2  # 20% scholarship example
                self.final_amount = self.amount_due - self.scholarship_reduction
                self.save()
                break
        else:
            self.final_amount = self.amount_due

    def __str__(self):
        return f"{self.student.username} - {self.final_amount} due"

class Payment(models.Model):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)  # From PayPal
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fee.student.username} - {self.payment_id} - {self.is_successful}" 
    

# views.py

