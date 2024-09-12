from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from adminapp.models import SchoolUser, Subject, Course, ExamResult, Exam, Session , Leave
from staffapp.models import Attendance
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.contrib.auth.models import User, auth
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Count


# cache
def clear_all_cache():
    cache.clear()


# staff home
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def staff_dashboard(request):
    subjects_assigned_count = Subject.objects.filter(
        staff_assigned=request.user
    ).count()
    students_count = (
        SchoolUser.objects.filter(subjects_enrolled__staff_assigned=request.user)
        .distinct()
        .count()
    )
    attendance_count = Attendance.objects.filter(
        subject__staff_assigned=request.user
    ).count()
    context = {
        "staff_name": request.user.username,
        "subjects_assigned_count": subjects_assigned_count,
        "students_count": students_count,
        "attendance_count": attendance_count,
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
def staff_logout(request):
    auth.logout(request)
    messages.success(request, "You have been logged out.")
    clear_all_cache()
    return render(request, "staff_templates/staff_login.html")


# take attendence
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
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

            # Check if the attendance date is in the past
            if attendance_date < timezone.now().date():
                messages.error(
                    request, "Previous dates cannot be selected for attendance."
                )
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
def view_attendance(request):
    subjects = Subject.objects.filter(staff_assigned=request.user)
    return render(
        request,
        "staff_templates/update_attendance_template.html",
        {
            "subjects": subjects,
        },
    )


def view_results(request):
    return render(
        request,
        "staff_templates/add_result_template.html",
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

            print(f"Fetching students for Subject ID: {subject_id} ")

            if subject_id:
                # Fetch the selected subject
                selected_subject = get_object_or_404(
                    Subject, id=subject_id, staff_assigned=request.user
                )
                selected_subject_id = subject_id
                students = selected_subject.students.filter(role="student")

                # Fetch related sessions and exams

                exams = Exam.objects.all()

        elif "save_result" in request.POST:
            subject_id = request.POST.get("subject")

            exam_id = request.POST.get("exam")
            student_id = request.POST.get("student_id")
            assignment_marks = request.POST.get("assignment_marks")
            exam_marks = request.POST.get("exam_marks")

            print(
                f"Saving result with Subject ID: {subject_id}, Exam ID: {exam_id}, Student ID: {student_id}, Assignment Marks: {assignment_marks}, Exam Marks: {exam_marks}"
            )

            if (
                subject_id
                and exam_id
                and student_id
                and assignment_marks
                and exam_marks
            ):
                selected_subject = get_object_or_404(
                    Subject, id=subject_id, staff_assigned=request.user
                )

                try:
                    selected_exam = Exam.objects.get(
                        id=exam_id,
                        subject=selected_subject,
                    )
                    print(f"Exam found: {selected_exam}")
                except Exam.DoesNotExist:
                    print(f"Exam not found - ID: {exam_id}, Subject ID: {subject_id}")
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
                return redirect(
                    "add_result"
                )  # Redirect to the same page to reset form and show messages
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