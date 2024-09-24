from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login,logout 
from django.contrib import messages
from django.contrib.auth.models import User, auth
from adminapp.models import ExamResult, SchoolUser,Subject,Leave,Feedback,Course
from staffapp.models import Attendance,get_attendance_statistics
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.contrib.auth.hashers import make_password
from adminapp.views import home
from django.utils import timezone
from django.db.models import Sum
from paymentapp.models import Fee,Payment


# student login
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def student_login(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            if not request.user.is_approved:
                logout(request)
                messages.warning(request, "Your approval is pending. Please contact the admin.")
                return redirect('student_login')
            return redirect('student_dashboard')
        else:          
            return render(request, 'student_login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'student_login.html')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if user.is_approved:
                login(request, user)
                messages.success(request, 'You are logged in.')
                return redirect('student_dashboard')
            else:
                messages.warning(request, "Your approval is pending. Please contact the admin.")
                return render(request, 'student_login.html')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'student_login.html')
    
    return render(request, 'student_login.html')

# student dashboard 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def student_dashboard(request):
    student = request.user
    # Calculate attendance
    total_present_days = Attendance.objects.filter(student=student, status=True).count()
    total_absent_days = Attendance.objects.filter(student=student, status=False).count()
    total_days = Attendance.objects.filter(student=student).values_list('date', flat=True).distinct().count()

    # Fetch subjects and attendance by subject
    subjects = Subject.objects.filter(students=student)
    attendance_by_subject_data = []
    subjects_labels = []

    for subject in subjects:
        attendance_count = Attendance.objects.filter(student=student, subject=subject, status=True).count()
        attendance_by_subject_data.append(attendance_count)
        subjects_labels.append(subject.name)
    
    # Fetch marks for each subject
    marks_data = []
    subjects_marks_labels = []
    
    for subject in subjects:
        # Assuming you have a way to get the student's marks for each subject
        marks = ExamResult.objects.filter(student=student, exam__subject=subject).aggregate(marks=Sum('marks_obtained'))['marks'] or 0
        marks_data.append(marks)
        subjects_marks_labels.append(subject.name)
    
    # Count total students, staff, courses, and subjects
    student_count = SchoolUser.objects.filter(role='student').count()
    staff_count = SchoolUser.objects.filter(role='staff').count()
    subject_count = Subject.objects.count()

    # Count total leaves taken by the student
    total_leaves_taken = Leave.objects.filter(user=student).count()

    context = {
        'total_present_days': total_present_days,
        'total_absent_days': total_absent_days,
        'total_days': total_days,
        'attendance_by_subject_data': attendance_by_subject_data,
        'subjects_labels': subjects_labels,
        'student_count': student_count,
        'staff_count': staff_count,
        'subject_count': subject_count,
        'marks_data': marks_data,
        'subjects_marks_labels': subjects_marks_labels,
        'total_leaves_taken': total_leaves_taken,  # Add this line
    }

    return render(request, 'student_home_template.html', context)




# student register
@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def register_student(request):
    if request.method == "POST":
        # Extract data from the form
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        course_id = request.POST.get("course_id")
        profile_photo = request.FILES.get("profile_photo")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Validate the data
        if not (
            first_name
            and last_name
            and username
            and email
            and phone
            and password1
            and password2
            and course_id
        ):
            messages.error(request, "Please fill in all required fields.")
            return redirect("register_student")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("register_student")

        # Check if the username or email already exists
        if SchoolUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register_student")

        if SchoolUser.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register_student")

        try:
            # Retrieve the selected course
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            messages.error(request, "Selected course does not exist.")
            return redirect("register_student")

        # Create and save the student
        student = SchoolUser(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone=phone,
            address=address,
            profile_photo=profile_photo,
            role="student",
        )
        student.set_password(password1)  # Hash the password
        student.save()

        # Enroll the student in the selected course
        course.enroll_student(student)

        # Provide feedback to the user
        messages.success(
            request,
            "Data received, please wait for admin approval."
        )
        return redirect("student_login")

    # If GET request, render the registration page
    courses = Course.objects.all()
    context = {
        "courses": courses,
    }

    return render(request, "student_register.html", context)


# cache 
def clear_all_cache():
    cache.clear() 
    
    
# logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True) 
def student_logout(request):
    auth.logout(request)  
    messages.success(request, 'You have been logged out.')
    clear_all_cache()
    return render(request, 'student_login.html') 

# fetching the result
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def result_view(request):
    student = get_object_or_404(SchoolUser, username=request.user.username, role='student')

    results = ExamResult.objects.filter(student=student)

    results = results.select_related('exam__subject', 'exam__course', 'exam__session')

    # Pass the results to the template
    return render(
        request,
        'student_view_result.html',
        {'results': results}
    ) 

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required    
def attendance_view(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Validate the dates
        if not start_date or not end_date:
            messages.error(request, 'Please select both start and end dates.')
            return redirect('attendance_view')

        start_date = parse_date(start_date)
        end_date = parse_date(end_date)

        if not start_date or not end_date:
            messages.error(request, 'Invalid date format.')
            return redirect('attendance_view')

        if start_date > end_date:
            messages.error(request, 'Start date cannot be later than end date.')
            return redirect('attendance_view')

        # Check if end_date is in the future
        if end_date > timezone.now().date():
            messages.error(request, 'Future dates cannot be selected.')
            return redirect('attendance_view')

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            messages.error(request, 'Subject not found.')
            return redirect('attendance_view')

        # Filter attendance for the logged-in student, selected subject, and date range
        attendance_data = Attendance.objects.filter(
            subject=subject,
            student=request.user,  # Only fetch attendance for the logged-in student
            date__range=[start_date, end_date]
        )

        total_days = (end_date - start_date).days + 1
        present_days = attendance_data.filter(status=True).count()  # Count only present days
        absent_days = attendance_data.filter(status=False).count()  # Count absent days

        context = {
            'subjects': Subject.objects.filter(course__students=request.user),  # Filter relevant subjects
            'attendance_data': attendance_data,
            'selected_subject': subject,
            'start_date': start_date,
            'end_date': end_date,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
        }

        return render(request, 'student_view_attendance.html', context)

    else:
        # Fetch only subjects relevant to the student's course
        subjects = Subject.objects.filter(course__students=request.user)  # Fetch subjects based on enrolled course
        context = {
            'subjects': subjects,
        }
        return render(request, 'student_view_attendance.html', context)
   
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required   
def password_reset(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if role != 'student':
            messages.error(request, 'Only students are allowed to reset their passwords.')
            return redirect('password_reset')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('password_reset')

        try:
            user = SchoolUser.objects.get(username=username, role='student')
            user.password = make_password(new_password)
            user.save()

            messages.success(request, 'Password reset successfully!')
            return redirect('home')  

        except SchoolUser.DoesNotExist:
            messages.error(request, 'Student with the provided username does not exist.')
            return redirect('password_reset')

    return render(request, 'reset_password.html')


def student_apply_leave(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')

        # Ensure the start and end dates are valid
        if start_date and end_date and reason:
            try:
                start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()

                if start_date > end_date:
                    messages.error(request, "End date cannot be before start date.")
                else:
                    # Create a new leave request
                    leave = Leave.objects.create(
                        user=request.user,
                        start_date=start_date,
                        end_date=end_date,
                        reason=reason,
                        status='pending',
                        applied_at=timezone.now()
                    )
                    leave.save()
                    messages.success(request, "Your leave request has been submitted.")
                    
                    # Print the start date, end date, and reason for debugging
                    print(f"Start Date: {start_date}, End Date: {end_date}, Reason: {reason}")

                    return redirect('student_apply_leave')  # Redirect to avoid resubmission issues

            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
        else:
            messages.error(request, "All fields are required.")

    # Fetch all leave requests for the current user
    leaves = Leave.objects.filter(user=request.user)
    context = {
        'leaves': leaves,
    }

    return render(request, 'student_apply_leave.html', context) 


def student_feedback(request):
    all_feedback = Feedback.objects.all().order_by('-created_at')  # Order by newest first
    if request.method == 'POST':
        feedback_text = request.POST.get('feedback')
        if feedback_text:
            Feedback.objects.create(
                sender_role='student',
                sender=request.user,
                feedback=feedback_text,
                created_at=timezone.now()
            )
            messages.success(request, "Your feedback has been submitted successfully.")
            return redirect('student_feedback')  # Redirect to the same feedback form
        else:
            messages.error(request, "Please enter some feedback before submitting.")
    context = {
        'all_feedback': all_feedback
    }
    return render(request,'student_feedback.html',context) 


def student_profile_update(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        address = request.POST.get('address')
        password1 = request.POST.get('password1')
        # update user details
        user = SchoolUser.objects.update_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password1,
            address = address,
        )
        user.role = 'student'
        user.save()

        messages.success(request, "Student details updated successfully.")
        return redirect('admin_dashboard') 
    return render(request,'student_profile.html') 


def fee_section(request):
    if request.user.is_authenticated:  
        student_id = request.user.id  
        fees = Fee.objects.filter(student__id=student_id)

        context = {
            'fees': fees,
        }

        return render(request, 'fee_view_template.html', context) 
    else:
       
        return redirect('login') 
    
    
# password reseting
def forgot_password_request(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        
        try:
            # Check if the user with the provided username exists
            user = SchoolUser.objects.get(username=username)
            
            # Redirect to password reset form with the username
            return redirect('reset_password', username=username)

        except SchoolUser.DoesNotExist:
            messages.error(request, 'Invalid username. Please try again.')

    return render(request, 'forgot_password_request.html')  


def reset_password(request, username):
    try:
        # Get the user with the provided username
        user = SchoolUser.objects.get(username=username)

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                # Set the new password
                user.set_password(new_password)
                user.save()

                messages.success(request, 'Password reset successful. You can now log in.')
                return redirect('student_login')

            else:
                messages.error(request, 'Passwords do not match.')

        return render(request, 'reset_password.html', {'username': username})

    except SchoolUser.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('forgot_password_request') 