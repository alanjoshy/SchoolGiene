from django.db import models
from adminapp.models import SchoolUser,ExamResult
# Create your models here. 
class Fee(models.Model):
    student = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)  
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update when the instance is saved


    def __str__(self):
        return f"{self.student.username} - {self.amount} due"

class Payment(models.Model):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)  # From PayPal
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fee.student.username} - {self.payment_id} - {self.is_successful}" 
    

# views.py

