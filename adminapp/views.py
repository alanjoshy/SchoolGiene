from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from adminapp.models import SchoolUser, Course, Subject, Session, Exam, ExamResult,Leave
from django.contrib.auth.models import User, auth
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.utils import timezone


# cache
def clear_all_cache():
    cache.clear()


# clear cookies from django
def clear_all_cookies(response):
    for cookie in response.cookies:
        response.delete_cookie(cookie)
    return response


# home page
def home(request):
    return render(request, "admin_templates/home.html")


# adminlogin
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):

    if request.method == "GET":
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect("admin_dashboard")
            else:
                messages.error(request, "You do not have admin privileges.")
                logout(request)
                return redirect("admin_login")
        return render(request, "admin_templates/admin_login.html")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "admin_templates/admin_login.html")

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_superuser:  # Check if the user is a superuser
                login(request, user)
                messages.success(request, f"{username} logged in.")
                return redirect("admin_dashboard")
            else:
                messages.error(request, "You do not have admin privileges.")
                return render(request, "admin_templates/admin_login.html")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "admin_templates/admin_login.html")

    return render(request, "admin_templates/admin_login.html")


# admin dashboard
@login_required(login_url="admin_login")
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("admin_login")  # Redirect if the user is not a superuser

    # students count
    student_count = SchoolUser.objects.filter(role="student").count()

    # staff count
    staff_count = SchoolUser.objects.filter(role="staff").count()

    # course count
    courses = Course.objects.all()
    course_count = courses.count()

    # Get course names and the count of subjects in each course
    course_subject_counts = []
    for course in courses:
        subject_count = Subject.objects.filter(course=course).count()
        course_subject_counts.append(
            {"course_name": course.name, "subject_count": subject_count}
        )

    # subject count
    subject_count = Subject.objects.all().count()

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
        "course_count": course_count,
        "subject_count": subject_count,
        "course_subject_counts": course_subject_counts,  # Pass course and subject count data
    }

    return render(request, "admin_templates/home_content.html", context)


# admin logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_logout(request):
    auth.logout(request)
    messages.success(request, "You have been logged out.")
    clear_all_cache()
    return render(request, "admin_templates/admin_login.html")


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_student(request):
    if request.method == "POST":
        student_id = request.POST.get("delete_student_id")
        if student_id:
            student = get_object_or_404(SchoolUser, id=student_id, role="student")
            student.delete()
            messages.success(request, "Student has been successfully deleted!")
            return redirect(
                "manage_student"
            )  # Redirect to the same page to update the list

    # Fetch all students
    students = SchoolUser.objects.filter(role="student")
    student_count = students.count()

    context = {
        "students": students,
        "student_count": student_count,
    }
    return render(request, "admin_templates/manage_student_template.html", context)


# student approval
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def approve_student(request, student_id):
    student = get_object_or_404(SchoolUser, id=student_id)
    student.is_approved = True
    student.save()
    messages.success(request, "Student has been approved.")
    return redirect("manage_student")


# staff register
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def staff_register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
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

        # Create the staff user
        user = SchoolUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password1,
            phone=phone,
            profile_photo=photo,
            address=address,
        )

        # Set role to 'staff'
        user.role = "staff"
        user.save()

        messages.success(request, "Staff registered successfully.")
        return redirect("admin_dashboard")

    return render(request, "admin_templates/staff_register_template.html")


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_staff(request):
    if request.method == "POST":
        # Handle staff deletion
        if "delete_staff_id" in request.POST:
            staff_id = request.POST.get("delete_staff_id")
            if staff_id:
                try:
                    staff_member = SchoolUser.objects.get(id=staff_id, role="staff")

                    # Check if the staff member is assigned to any subjects
                    assigned_subjects = Subject.objects.filter(staff_assigned=staff_member)
                    if assigned_subjects.exists():
                        messages.error(
                            request,
                            "Staff has been assigned to subjects. Please reassign another staff to that subject and then delete.",
                        )
                    else:
                        staff_member.delete()
                        messages.success(request, "Staff member deleted successfully.")

                except SchoolUser.DoesNotExist:
                    messages.error(request, "Staff member not found.")

            # Refresh the page after deletion
            return redirect("manage_staff")

        # Handle staff update
        elif "staff_id" in request.POST:
            staff_id = request.POST.get("staff_id")
            staff = get_object_or_404(SchoolUser, id=staff_id, role="staff")

            # Update staff details, preserving the staff ID
            staff.first_name = request.POST.get("first_name", staff.first_name)
            staff.last_name = request.POST.get("last_name", staff.last_name)
            staff.username = request.POST.get("username", staff.username)
            staff.email = request.POST.get("email", staff.email)
            staff.phone = request.POST.get("phone", staff.phone)
            staff.address = request.POST.get("address", staff.address)

            if "profile_photo" in request.FILES:
                staff.profile_photo = request.FILES["profile_photo"]

            if "password1" in request.POST and request.POST.get("password1"):
                if request.POST.get("password1") == request.POST.get("password2"):
                    staff.password = make_password(request.POST.get("password1"))
                else:
                    messages.error(request, "Passwords do not match.")
                    return redirect("manage_staff")

            staff.save()
            messages.success(request, "Staff member updated successfully.")
            return redirect("manage_staff")

    # Fetch all staff members
    staff = SchoolUser.objects.filter(role="staff")
    # Count staff members
    staff_count = staff.count()

    context = {
        "staff_members": staff,
        "staff_count": staff_count,
    }
    return render(request, "admin_templates/manage_staff_template.html", context)


def add_subject(request):
    return render(request, "admin_templates/add_subject_template.html")


def add_student(request):
    return render(request, "admin_templates/add_student_template.html")


# def add_course(request):
#     if request.method == "POST":
#         course_name = request.POST.get("course_name")
#         # course_description = request.POST.get('description')

#         # Create the course
#         course = Course.objects.create(name=course_name)
#         messages.success(request, f"{course_name} created..")

#         # Optional: You can enroll students right after creating the course
#         # # Assuming you have a list of student IDs you want to enroll
#         # student_ids = request.POST.getlist('students')
#         # students = SchoolUser.objects.filter(id__in=student_ids, role='student')

#         # for student in students:
#         #     course.enroll_student(student)

#         # return redirect('course_list')  # Redirect to the course list page or any other page after creation

#     return render(request, "admin_templates/add_course_template.html")


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_course(request):
    if request.method == "POST":
        course_name = request.POST.get("course_name")
        class_teacher_id = request.POST.get("class_teacher")

        class_teacher = SchoolUser.objects.get(id=class_teacher_id, role="staff")

        course = Course.objects.create(name=course_name, class_teacher=class_teacher)
        messages.success(
            request,
            f"{course_name} created with {class_teacher.username} as the class teacher.",
        )

        return redirect("manage_course")

    teachers = SchoolUser.objects.filter(role="staff")

    return render(
        request, "admin_templates/add_course_template.html", {"teachers": teachers}
    )


# manage course
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_course(request):
    if request.method == "POST":
        delete_course_id = request.POST.get("delete_course_id")
        if delete_course_id:
            course = get_object_or_404(Course, id=delete_course_id)
            enrolled_students = SchoolUser.objects.filter(
                courses_enrolled=course, role="student"
            )

            if enrolled_students.exists():
                messages.error(
                    request,
                    "Students are enrolled in this course. Please move the students to another course or delete the students before deleting the course.",
                )
                # You can redirect to a specific page where the user can manage student reassignment
                return redirect("manage_course")
            else:
                course.delete()
                messages.success(request, "Course has been successfully deleted!")
                return redirect(
                    "manage_course"
                )  # Redirect to the same page to refresh the list

    courses = Course.objects.all()
    assigned_staff = Course.objects.all().select_related("class_teacher")
    context = {"courses": courses, "assigned_staff": assigned_staff}
    return render(request, "admin_templates/manage_course_template.html", context)


# add subject
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_subject(request):
    if request.method == "POST":
        # Retrieve data from the form
        subject_name = request.POST.get("subject_name")
        course_id = request.POST.get("course_id")
        staff_id = request.POST.get("staff_id")

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            messages.error(request, "Selected course does not exist.")
            return redirect("add_subject")  # Redirect back to form

        try:
            staff = SchoolUser.objects.get(id=staff_id)
        except SchoolUser.DoesNotExist:
            messages.error(request, "Selected staff member does not exist.")
            return redirect("add_subject")

        # Create the new subject
        subject = Subject.objects.create(
            name=subject_name, course=course, staff_assigned=staff
        )

        # Enroll students in the new subject
        students = course.students.all()
        subject.students.set(students)  # Add students to the new subject

        messages.success(
            request,
            f'Subject "{subject_name}" created and assigned to {staff.username}. Students enrolled in the course have been added to the subject.',
        )
        return redirect("add_subject")

    courses = Course.objects.all()
    staff_members = SchoolUser.objects.filter(role="staff")

    context = {
        "courses": courses,
        "staff_members": staff_members,
    }
    return render(request, "admin_templates/add_subject_template.html", context)


# manage subjects
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_subject(request):
    if request.method == "POST":
        delete_subject_id = request.POST.get("delete_subject_id")
        if delete_subject_id:
            try:
                subject = get_object_or_404(Subject, id=delete_subject_id)
                subject.delete()
                messages.success(request, "Subject has been successfully deleted!")
            except Subject.DoesNotExist:
                messages.error(request, "Subject does not exist.")
            return redirect("manage_subject")  # Redirect to refresh the list

    subjects = Subject.objects.select_related("course", "staff_assigned").all()
    context = {"subjects": subjects}
    return render(request, "admin_templates/manage_subject_template.html", context)


# register student
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
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

        # Validate the data (add your own validation logic as needed)
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
            f"Student {first_name} {last_name} with {username}has been registered and enrolled in {course.name}.",
        )
        return redirect(
            "register_student"
        )  # Redirect to the student list or another page

    # If GET request, render the registration page
    courses = Course.objects.all()
    context = {
        "courses": courses,
    }

    return render(request, "admin_templates/add_student_template.html", context)


# add session
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_session(request):
    if request.method == "POST":
        session_name = request.POST.get("session_name")
        session_start_year = request.POST.get("session_start_year")
        session_end_year = request.POST.get("session_end_year")

        if session_name and session_start_year and session_end_year:
            # Convert session_start_year and session_end_year to integers
            start_year = int(session_start_year.split("-")[0])
            end_year = int(session_end_year.split("-")[0])

            # Create and save the session
            session = Session.objects.create(
                name=session_name,
                start_year=start_year,
                end_year=end_year,
            )
            messages.success(request, "Session created successfully!")
            return redirect(
                "manage_session"
            )  # Redirect to the session list view or any other view
        else:
            messages.error(request, "Please fill out all fields.")
    return render(request, "admin_templates/add_session_template.html")


# manage session
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_session(request):
    if request.method == "POST":
        delete_session_id = request.POST.get("delete_session_id")
        if delete_session_id:
            try:
                session = get_object_or_404(Session, id=delete_session_id)
                session.delete()
                messages.success(request, "Session has been successfully deleted!")
            except Session.DoesNotExist:
                messages.error(request, "Session does not exist.")
            return redirect("manage_session")  # Redirect to refresh the list

    sessions = Session.objects.all()
    return render(
        request, "admin_templates/manage_session_template.html", {"sessions": sessions}
    )


# add exam
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_exam(request):
    if request.method == "POST":
        name = request.POST.get("name")
        session_id = request.POST.get("session")
        course_id = request.POST.get("course")
        subject_id = request.POST.get("subject")
        exam_date = request.POST.get("exam_date")

        # Fetch related objects
        session = get_object_or_404(Session, id=session_id)
        course = get_object_or_404(Course, id=course_id)
        subject = get_object_or_404(Subject, id=subject_id)

        # Create and save the exam
        exam = Exam.objects.create(
            name=name,
            session=session,
            course=course,
            subject=subject,
            exam_date=exam_date,
        )
        return redirect("manage_exam")

    sessions = Session.objects.all()
    courses = Course.objects.all()
    subjects = Subject.objects.all()
    return render(
        request,
        "admin_templates/add_exam_template.html",
        {"sessions": sessions, "courses": courses, "subjects": subjects},
    )


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_exam(request):
    if "delete" in request.GET:
        exam_id = request.GET.get("delete")
        exam = get_object_or_404(Exam, id=exam_id)
        exam.delete()
        messages.success(request, "Exam deleted successfully.")
        return redirect("manage_exam")

    exams = Exam.objects.all()
    return render(
        request, "admin_templates/manage_exam_template.html", {"exams": exams}
    )


def view_attendance(request):
    return render(request,"admin_templates/admin_view_attendance.html") 


def student_view_leave(request):
    # Fetch all leave requests where the user role is 'student'
    leave_requests = Leave.objects.filter(user__role='student')

    context = {
        'leaves': leave_requests,
    }

    return render(request, "admin_templates/student_leave_view.html", context)


def staff_view_leave(request):
    leave_requests = Leave.objects.filter(user__role='staff')

    context = {
        'leaves': leave_requests,
    }
    return render(request,"admin_templates/staff_leave_view.html",context)


def student_update_leave_status(request, leave_id):
    # Get the leave request by ID
    leave_request = get_object_or_404(Leave, id=leave_id)

    # Check if the status is being updated
    status = request.GET.get('status')

    if status in ['approved', 'rejected']:
        leave_request.status = status
        leave_request.approved_at = timezone.now()  # Set the timestamp for when the leave was approved or rejected
        leave_request.save()

        # Display a success message
        messages.success(request, f"Leave request has been {status} successfully.")
    else:
        # Display an error message if the status is invalid
        messages.error(request, "Invalid status update.")

    # Redirect to the leave request list view
    if leave_request.user.role == 'student':
        return redirect('student_view_leave')
    else:
        return redirect('staff_view_leave') 
    
    
def staff_update_leave_status(request, leave_id):
    # Get the leave request by ID
    leave_request = get_object_or_404(Leave, id=leave_id)

    # Check if the status is being updated
    status = request.GET.get('status')

    if status in ['approved', 'rejected']:
        # Update the leave status
        leave_request.status = status
        leave_request.approved_at = timezone.now()  # Set the timestamp for when the leave was approved or rejected
        leave_request.save()

        # Display a success message
        messages.success(request, f"Leave request has been {status} successfully.")
    else:
        # Display an error message if the status is invalid
        messages.error(request, "Invalid status update. Please try again.")

    # Redirect to the leave request list view
    return redirect('staff_view_leave') 


def admin_student_feedback(request):
    return render(request,"admin_templates/student_feedback_template.html") 


def admin_staff_feedback(request):
    return render(request,"admin_templates/staff_feedback_template.html") 