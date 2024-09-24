from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from adminapp.models import SchoolUser, Subject, Course, ExamResult, Exam, Session , Leave,Feedback
from staffapp.models import Attendance
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.contrib.auth.models import User, auth
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils.timezone import now
from django.core.mail import send_mail
from django.urls import reverse
import random
import string


# cache
def clear_all_cache():
    cache.clear()


# staff home
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def staff_dashboard(request):
    # Get the current year
    current_year = now().year

    # Leave data for the current year
    leave_data = (
        Leave.objects.filter(user=request.user, start_date__year=current_year)
        .values('start_date__month')
        .annotate(total_leaves=Count('id'))
        .order_by('start_date__month')
    )

    # Initialize the months and leave counts
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    leave_count_by_month = [0] * 12  # Initialize counts for each month (0 - 11)

    # Populate the leave counts
    for data in leave_data:
        month_index = data['start_date__month'] - 1  # 0-based index for months
        leave_count_by_month[month_index] = data['total_leaves']
    
    # Subject view
    subjects = Subject.objects.filter(staff_assigned=request.user)
    subject_names = []
    student_counts = []

    for subject in subjects:
        count = SchoolUser.objects.filter(subjects_enrolled=subject).count()
        subject_names.append(subject.name)
        student_counts.append(count)

    # Count total students, staff, courses, and subjects
    subjects_assigned_count = subjects.count()
    students_count = SchoolUser.objects.filter(subjects_enrolled__in=subjects).distinct().count()
    attendance_count = Attendance.objects.filter(subject__in=subjects).count()

    # Count total leaves taken by the staff member
    total_leaves_taken = Leave.objects.filter(user=request.user).count()

    context = {
        "staff_name": request.user.username,
        "subjects_assigned_count": subjects_assigned_count,
        "students_count": students_count,
        "attendance_count": attendance_count,
        'leave_count_by_month': leave_count_by_month,
        'months': months,
        'subject_names': subject_names,
        'student_counts': student_counts,
        'total_leaves_taken': total_leaves_taken,  # Add this line
    }
    
    return render(request, "staff_templates/staff_home_template.html", context)

# staff registration
@cache_control(no_cache=True, must_revalidate=True, no_store=True)

def staff_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        photo = request.FILES.get("photo")  # Handle file upload
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("staff_register")

        if SchoolUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("staff_register")

        if SchoolUser.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("staff_register")

        # Create the user
        user = SchoolUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            phone=phone,
            profile_photo=photo,
        )

        # Ensure that the role is set to 'staff'
        user.role = "staff"
        user.save()

        messages.success(request, "Staff registered successfully.")
        return redirect("admin_dashboard")
    return render(request, "staff_templates/staff_register.html")


# staff login section
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def staff_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect("staff_login")

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.role == "staff":  # Check if the user has the role of 'staff'
                login(request, user)
                messages.success(request, "You are logged in.")
                return redirect("staff_dashboard")
            else:
                messages.error(request, "You are not authorized to access this page.")
                return redirect("staff_login")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("staff_login")

    elif request.method == "GET":
        if request.user.is_authenticated and request.user.role == "staff":
            return redirect("staff_dashboard")
        return render(request, "staff_templates/staff_login.html")


# admin logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def staff_logout(request):
    auth.logout(request)
    messages.success(request, "You have been logged out.")
    clear_all_cache()
    return render(request, "staff_templates/staff_login.html")


# take attendence
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def take_attendance(request):
    subjects = Subject.objects.filter(staff_assigned=request.user)
    students = []

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        attendance_date = request.POST.get("attendance_date")

        if attendance_date:
            # Convert the attendance_date from string to a date object
            try:
                attendance_date = timezone.datetime.strptime(
                    attendance_date, "%Y-%m-%d"
                ).date()
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return redirect("take_attendance")

            # Check if the attendance date is in the future
            if attendance_date > timezone.now().date():
                messages.error(request, "Future dates cannot be selected for attendance.")
                return redirect("take_attendance")

        if subject_id and attendance_date:
            # Fetch the subject and enrolled students
            selected_subject = get_object_or_404(
                Subject, id=subject_id, staff_assigned=request.user
            )
            students = selected_subject.students.all()

            if "save_attendance" in request.POST:
                present_student_ids = request.POST.getlist("student_data[]")

                # Iterate over all students enrolled in the subject
                for student in students:
                    is_present = str(student.id) in present_student_ids
                    Attendance.objects.update_or_create(
                        student=student,
                        subject=selected_subject,
                        date=attendance_date,
                        defaults={"status": is_present},
                    )

                messages.success(
                    request, "Attendance data has been successfully saved!"
                )
                return redirect("take_attendance")
            else:
                messages.error(
                    request, "Failed to save attendance data. Please try again."
                )
        else:
            messages.error(request, "Please select a subject and date.")
    else:
        messages.info(request, "Please select a subject and date to fetch students.")

    return render(
        request,
        "staff_templates/take_attendance_template.html",
        {
            "subjects": subjects,
            "students": students,
        },
    )


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def view_student_attendance(request):
    # Fetch all courses and initialize variables
    courses = Course.objects.all()
    subjects = []
    attendance_data = []
    selected_course_id = None
    selected_subject_id = None
    start_date = None
    end_date = None
    error_message = None

    # Get the logged-in staff user
    staff_user = request.user  # Assuming the user is authenticated and is a staff member

    if request.method == "POST":
        # Get form data
        selected_course_id = request.POST.get('course')
        selected_subject_id = request.POST.get('subject')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Check if end_date is in the future
        if end_date and timezone.now().date() < timezone.datetime.strptime(end_date, '%Y-%m-%d').date():
            error_message = "Future dates cannot be selected."
        else:
            # Fetch subjects related to the selected course that are assigned to the staff
            if selected_course_id:
                subjects = Subject.objects.filter(course_id=selected_course_id, staff_assigned=staff_user)

            # If subject, start date, and end date are provided, fetch the attendance data
            if selected_subject_id and start_date and end_date:
                attendance_data = Attendance.objects.filter(
                    subject_id=selected_subject_id,
                    date__range=[start_date, end_date],
                    subject__staff_assigned=staff_user  # Ensure the subject is assigned to the staff
                ).select_related('student', 'subject')

                # If no attendance data is found, set an error message
                if not attendance_data.exists():
                    error_message = "No attendance data found for the selected date range."

    # Prepare attendance data for rendering
    attendance_records = []
    for attendance in attendance_data:
        # Fetch student name and attendance status
        student_name = attendance.student.first_name if attendance.student else "Unknown Student"
        attendance_records.append({
            'student_name': student_name,
            'status': "Present" if attendance.status else "Absent",  # Convert boolean to string
            'date': attendance.date,
        })

    context = {
        'courses': courses,
        'subjects': subjects,
        'selected_course_id': selected_course_id,
        'selected_subject_id': selected_subject_id,
        'start_date': start_date,
        'end_date': end_date,
        'attendance_data': attendance_records,
        'error_message': error_message,
    }

    # Render the template with the context
    return render(request, "staff_templates/staff_view_attendance.html", context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def view_results(request):
    subjects = Subject.objects.filter(staff_assigned=request.user)
    results = []

    if request.method == "POST":
        subject_id = request.POST.get("subject")

        if subject_id:
            selected_subject = get_object_or_404(Subject, id=subject_id, staff_assigned=request.user)
            # Fetch exams for the selected subject
            exams = Exam.objects.filter(subject=selected_subject)

            # Fetch exam results for each exam and their enrolled students
            for exam in exams:
                exam_results = ExamResult.objects.filter(exam=exam).select_related('student')
                for result in exam_results:
                    results.append({
                        'student': result.student,
                        'exam': exam,
                        'assignment_marks': result.assignment_marks,
                        'marks_obtained': result.marks_obtained,
                        'max_marks': result.max_marks,
                    })

    return render(
        request,
        "staff_templates/view_exam_results_template.html",{
            "subjects": subjects,
            "results": results,
        },
    )


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_result(request):
    subjects = Subject.objects.filter(staff_assigned=request.user)
    exams = []
    students = []
    selected_subject_id = None
    selected_exam_id = None

    if request.method == "POST":
        if "fetch_students" in request.POST:
            subject_id = request.POST.get("subject")

            if subject_id:
                selected_subject = get_object_or_404(
                    Subject, id=subject_id, staff_assigned=request.user
                )
                selected_subject_id = subject_id
                students = selected_subject.students.filter(role="student")
                exams = Exam.objects.all()

        elif "save_result" in request.POST:
            subject_id = request.POST.get("subject")
            exam_id = request.POST.get("exam")
            student_id = request.POST.get("student_id")
            assignment_marks = request.POST.get("assignment_marks")
            exam_marks = request.POST.get("exam_marks")

            if (
                subject_id
                and exam_id
                and student_id
                and assignment_marks
                and exam_marks
            ):
                if float(assignment_marks) < 0 or float(exam_marks) < 0:
                    messages.error(request, "Negative marks cannot be added for exam and assignment.")
                    return redirect("add_result")

                selected_subject = get_object_or_404(
                    Subject, id=subject_id, staff_assigned=request.user
                )

                try:
                    selected_exam = Exam.objects.get(
                        id=exam_id,
                        subject=selected_subject,
                    )
                except Exam.DoesNotExist:
                    messages.error(request, "The selected exam does not exist.")
                    return redirect("add_result")

                student = get_object_or_404(SchoolUser, id=student_id, role="student")

                # Save or update the result
                ExamResult.objects.update_or_create(
                    student=student,
                    exam=selected_exam,
                    defaults={
                        "assignment_marks": assignment_marks,
                        "marks_obtained": exam_marks,
                    },
                )

                messages.success(request, "Result has been successfully saved!")
                return redirect("add_result")
            else:
                messages.error(request, "Please fill in all fields to save the result.")
    else:
        messages.info(request, "Please select a subject to fetch sessions and exams.")

    return render(
        request,
        "staff_templates/add_result_template.html",
        {
            "subjects": subjects,
            "exams": exams,
            "students": students,
            "selected_subject_id": selected_subject_id,
            "selected_exam_id": selected_exam_id,
        },
    )

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def staff_apply_leave(request): 
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
    return render(request,'staff_templates/staff_apply_leave_template.html') 


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def staff_feedback(request):
    if request.method == "POST":
        feedback_message = request.POST.get('feedback_message')
        
        if feedback_message:
            feedback = Feedback(
                sender_role='staff',
                sender=request.user,
                feedback=feedback_message,
                created_at=timezone.now()
            )
            feedback.save()
            messages.success(request, "Feedback uploaded successfully.")
            return redirect('staff_feedback')  # Redirect to avoid form resubmission

    # Fetch all feedback sent by staff
    feedback_list = Feedback.objects.filter(sender_role='staff').order_by('-created_at')
    
    context = {
        'feedback_list': feedback_list,
    }
    
    return render(request, 'staff_templates/staff_feedback_template.html', context) 

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

    return render(request, 'staff_templates/forgot_password_request.html') 


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
                return redirect('staff_login')

            else:
                messages.error(request, 'Passwords do not match.')

        return render(request, 'staff_templates/reset_password.html', {'username': username})

    except SchoolUser.DoesNotExist:
        messages.error(request, 'User does not exist.')
        return redirect('forgot_password_request') 