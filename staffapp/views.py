from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from adminapp.models import SchoolUser, Subject
from staffapp.models import Attendance
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.contrib.auth.models import User, auth
from django.http import JsonResponse


# cache
def clear_all_cache():
    cache.clear()


# staff home
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def staff_dashboard(request):
    context = {
        "staff_name": request.user.username  # Use request.user to get the username of the logged-in user
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

        if subject_id and attendance_date:
            # Fetch the subject and enrolled students
            selected_subject = get_object_or_404(
                Subject, id=subject_id, staff_assigned=request.user
            )
            students = (
                selected_subject.students.all()
            )  # Assuming a ManyToMany relationship between Subject and Student

            if "save_attendance" in request.POST:
                present_student_ids = request.POST.getlist("student_data[]")

                # Iterate over all students enrolled in the subject
                for student in students:
                    is_present = str(student.id) in present_student_ids
                    Attendance.objects.update_or_create(
                        student=student,
                        subject=selected_subject,
                        date=attendance_date,
                        defaults={
                            "status": is_present
                        },  # Update or create attendance with the status
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


def view_attendance(request):
    subjects = Subject.objects.filter(staff_assigned=request.user)
    return render(
        request,
        "staff_templates/update_attendance_template.html",
        {
            "subjects": subjects,
        },
    )
