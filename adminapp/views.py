from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from adminapp.models import SchoolUser, Course, Subject, Session, Exam, ExamResult,Leave,Feedback
from staffapp.models import Attendance
from django.contrib.auth.models import User, auth
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password 
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.core.files.uploadedfile import InMemoryUploadedFile
import imghdr


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
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url="admin_login")
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect("admin_login")  # Redirect if the user is not a superuser

    # Students count
    student_count = SchoolUser.objects.filter(role="student").count()

    # Staff count
    staff_count = SchoolUser.objects.filter(role="staff").count()

    # Course count
    courses = Course.objects.all()
    course_count = courses.count()

    # Get course names and count of students in each course
    course_student_counts = []
    for course in courses:
        # Count the number of students enrolled in the course
        student_in_course_count = SchoolUser.objects.filter(courses_enrolled=course, role="student").count()

        # Append data to the list
        course_student_counts.append({
            "course_name": course.name,
            "student_count": student_in_course_count
        })

    # Subject count
    subject_count = Subject.objects.all().count()

    # Prepare the course names and student counts for passing to the template
    course_names = [course['course_name'] for course in course_student_counts]
    student_counts = [course['student_count'] for course in course_student_counts]

    context = {
        "student_count": student_count,
        "staff_count": staff_count,
        "course_count": course_count,
        "subject_count": subject_count,
        "course_names": course_names,  # List of course names for the chart
        "student_counts": student_counts  # List of student counts for the chart
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
    # Handle search query from the request
    search_query = request.GET.get('search', '')

    if request.method == "POST":
        # Handle student deletion
        student_id = request.POST.get("delete_student_id")
        if student_id:
            student = get_object_or_404(SchoolUser, id=student_id, role="student")
            student.delete()
            messages.success(request, "Student has been successfully deleted!")
            return redirect("manage_student")  # Refresh the page after deletion

        # Handle student update (course change)
        edit_student_id = request.POST.get("edit_student_id")
        course_id = request.POST.get("course_id")
        if edit_student_id and course_id:
            student = get_object_or_404(SchoolUser, id=edit_student_id, role="student")
            course = get_object_or_404(Course, id=course_id)
            student.course = course  # Update the student's course
            student.save()
            messages.success(request, f"{student.first_name} {student.last_name}'s course has been updated successfully!")
            return redirect("manage_student") 
        
    # Fetch all students with search functionality
    students = SchoolUser.objects.filter(role="student")
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Fetch all available courses for the dropdown
    courses = Course.objects.all()

    # Count total students and filtered students
    student_count = students.count()

    context = {
        "students": students,
        "courses": courses,  # Pass available courses to the template
        "student_count": student_count,
        "search_query": search_query,  # To retain search query in the input field
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

        # Check for password match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("staff_register")

        # Check if username already exists
        if SchoolUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("staff_register")

        # Check if email already exists
        if SchoolUser.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("staff_register")

        # Validate the uploaded file is an image
        if photo:
            file_type = imghdr.what(photo)
            if file_type not in ['jpeg', 'png', 'gif', 'bmp']:
                messages.error(request, "Uploaded file is not a valid image.")
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
        return redirect("staff_register")

    return render(request, "admin_templates/staff_register_template.html")

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_staff(request):
    search_query = request.GET.get('search', '')

    if request.method == "POST":
        # Handle staff deletion
        if "delete_staff_id" in request.POST:
            staff_id = request.POST.get("delete_staff_id")
            if staff_id:
                try:
                    staff_member = SchoolUser.objects.get(id=staff_id, role="staff")
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
            return redirect("manage_staff")

        # Handle staff update
        elif "staff_id" in request.POST:
            staff_id = request.POST.get("staff_id")
            staff = get_object_or_404(SchoolUser, id=staff_id, role="staff")

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

    staff = SchoolUser.objects.filter(role="staff")
    if search_query:
        staff = staff.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    staff_count = staff.count()

    context = {
        "staff_members": staff,
        "staff_count": staff_count,
        "search_query": search_query,
    }
    return render(request, "admin_templates/manage_staff_template.html", context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_subject(request):
    return render(request, "admin_templates/add_subject_template.html")

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
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
@require_http_methods(["GET", "POST"])
def manage_course(request):
    if request.method == "POST":
        if "delete_course_id" in request.POST:
            # Handle course deletion
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
                    return redirect("manage_course")
                else:
                    course.delete()
                    messages.success(request, "Course has been successfully deleted!")
                    return redirect("manage_course")

        elif "edit_course_id" in request.POST:
            # Handle course editing
            edit_course_id = request.POST.get("edit_course_id")
            if edit_course_id:
                course = get_object_or_404(Course, id=edit_course_id)
                course.name = request.POST.get("name")
                class_teacher_id = request.POST.get("class_teacher")
                course.class_teacher = get_object_or_404(SchoolUser, id=class_teacher_id)
                course.save()
                messages.success(request, "Course details have been successfully updated!")
                return redirect("manage_course")

    # Handle search functionality
    query = request.GET.get("search", "")
    if query:
        courses = Course.objects.filter(name__icontains=query)  # Search courses by name
    else:
        courses = Course.objects.all()

    staff_members = SchoolUser.objects.filter(role="staff")  # Fetch all staff members
    context = {
        "courses": courses,
        "staff_members": staff_members,
        "query": query,  # Pass the search query to the template
    }
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
    search_query = request.GET.get('search', '')

    if request.method == "POST":
        if 'delete_subject_id' in request.POST:
            delete_subject_id = request.POST.get("delete_subject_id")
            if delete_subject_id:
                try:
                    subject = get_object_or_404(Subject, id=delete_subject_id)
                    
                    # Check if there are any exams associated with the subject
                    if Exam.objects.filter(subject=subject).exists():
                        messages.error(request, "An exam has been added to this subject. Please delete the associated exams before deleting the subject.")
                    else:
                        subject.delete()
                        messages.success(request, "Subject has been successfully deleted!")
                except Subject.DoesNotExist:
                    messages.error(request, "Subject does not exist.")
                return redirect("manage_subject")  # Redirect to refresh the list

        elif 'edit_subject_id' in request.POST:
            edit_subject_id = request.POST.get("edit_subject_id")
            subject_name = request.POST.get("subject_name")
            course_id = request.POST.get("course_id")
            staff_id = request.POST.get("staff_id")

            if edit_subject_id:
                subject = get_object_or_404(Subject, id=edit_subject_id)
                subject.name = subject_name
                subject.course_id = course_id
                subject.staff_assigned_id = staff_id
                subject.save()
                messages.success(request, "Subject has been successfully updated!")
                return redirect("manage_subject")

    # Search functionality
    subjects = Subject.objects.select_related("course", "staff_assigned").all()
    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) | 
            Q(course__name__icontains=search_query) | 
            Q(staff_assigned__first_name__icontains=search_query) |
            Q(staff_assigned__last_name__icontains=search_query)
        )

    courses = Course.objects.all()
    staffs = SchoolUser.objects.filter(role='staff')
    context = {
        "subjects": subjects,
        "courses": courses,
        "staffs": staffs,
        "search_query": search_query,
    }
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
    query = request.GET.get("q", "")
    if query:
        sessions = Session.objects.filter(name__icontains=query)
    else:
        sessions = Session.objects.all()

    if request.method == "POST":
        # Handle session deletion
        delete_session_id = request.POST.get("delete_session_id")
        if delete_session_id:
            try:
                session = get_object_or_404(Session, id=delete_session_id)
                
                # Check if any exams are associated with this session
                if session.exams.exists():
                    messages.error(request, "This session has associated exams. Please delete the exams before deleting the session.")
                else:
                    session.delete()
                    messages.success(request, "Session has been successfully deleted!")
            except Session.DoesNotExist:
                messages.error(request, "Session does not exist.")
            return redirect("manage_session")

        # Handle session editing
        session_id = request.POST.get("session_id")
        if session_id:
            try:
                session = get_object_or_404(Session, id=session_id)
                session.name = request.POST.get("session_name")
                session.start_year = int(request.POST.get("start_year"))  # Ensure conversion to int
                session.end_year = int(request.POST.get("end_year"))  # Ensure conversion to int
                session.save()
                messages.success(request, "Session has been successfully updated!")
            except Exception as e:
                messages.error(request, f"Error updating session: {e}")
            return redirect("manage_session")

    return render(
        request, "admin_templates/manage_session_template.html", {
            "sessions": sessions,
            "search_query": query  # Pass the search query to the template
        }
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
    if request.method == "POST":
        if "exam_id" in request.POST:
            exam_id = request.POST.get("exam_id")
            try:
                exam = get_object_or_404(Exam, id=exam_id)
                exam.name = request.POST.get("name")
                exam.subject_id = request.POST.get("subject")
                exam.course_id = request.POST.get("course")
                exam.session_id = request.POST.get("session")
                exam.exam_date = request.POST.get("exam_date")
                exam.save()
                messages.success(request, "Exam updated successfully.")
            except Exception as e:
                messages.error(request, f"Error updating exam: {e}")
            return redirect("manage_exam")

        if "delete" in request.GET:
            exam_id = request.GET.get("delete")
            try:
                exam = get_object_or_404(Exam, id=exam_id)
                exam.delete()
                messages.success(request, "Exam deleted successfully.")
            except Exception as e:
                messages.error(request, f"Error deleting exam: {e}")
            return redirect("manage_exam")

    search_query = request.GET.get("search", "")
    exams = Exam.objects.filter(name__icontains=search_query)
    subjects = Subject.objects.all()
    courses = Course.objects.all()
    sessions = Session.objects.all()

    return render(request, "admin_templates/manage_exam_template.html", {
        "exams": exams,
        "subjects": subjects,
        "courses": courses,
        "sessions": sessions,
        "search_query": search_query
    })



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def view_attendance(request):
    # Fetch all courses and initialize variables
    courses = Course.objects.all()
    subjects = []
    attendance_data = []
    selected_course_id = None
    selected_subject_id = None
    start_date = None
    end_date = None
    error_message = None

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
            # Fetch subjects related to the selected course
            if selected_course_id:
                subjects = Subject.objects.filter(course_id=selected_course_id)

            # If subject, start date, and end date are provided, fetch the attendance data
            if selected_subject_id and start_date and end_date:
                attendance_data = Attendance.objects.filter(
                    subject_id=selected_subject_id,
                    date__range=[start_date, end_date]
                ).select_related('student', 'subject')

                # If no attendance data is found, set an error message
                if not attendance_data.exists():
                    error_message = "No attendance data found for the selected date range."

    context = {
        'courses': courses,
        'subjects': subjects,
        'selected_course_id': selected_course_id,
        'selected_subject_id': selected_subject_id,
        'start_date': start_date,
        'end_date': end_date,
        'attendance_data': [
            {
                'student_name': attendance.student.name,
                'subject_name': attendance.subject.name,
                'date': attendance.date,
                'status': "Present" if attendance.status else "Absent"
            } for attendance in attendance_data
        ],
        'error_message': error_message,
    }

    # Render the template with the context
    return render(request, "admin_templates/admin_view_attendance.html", context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def student_view_leave(request):
    # Fetch all leave requests where the user role is 'student'
    leave_requests = Leave.objects.filter(user__role='student')

    context = {
        'leaves': leave_requests,
    }

    return render(request, "admin_templates/student_leave_view.html", context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def staff_view_leave(request):
    leave_requests = Leave.objects.filter(user__role='staff')
    context = {
        'leaves': leave_requests, 
    }
    return render(request,"admin_templates/staff_leave_view.html",context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
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
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required   
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

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def admin_student_feedback(request):
    if request.method == "POST":
        feedback_id = request.POST.get('feedback_id')
        reply = request.POST.get('reply')

        if feedback_id and reply:
            feedback = get_object_or_404(Feedback, id=feedback_id)
            feedback.feedback_reply = reply
            feedback.reply_at = timezone.now()
            feedback.save()
            messages.success(request, "Reply sent successfully.")
            return redirect('admin_student_feedback')  # Redirect to avoid form resubmission

    # Fetching feedback only from students
    feedback_list = Feedback.objects.filter(sender_role='student')
    context = {
        'feedback_list': feedback_list,
    }
    return render(request, "admin_templates/student_feedback_template.html", context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def admin_staff_feedback(request):
    if request.method == "POST":
        feedback_id = request.POST.get('feedback_id')
        reply = request.POST.get('reply')

        if feedback_id and reply:
            feedback = get_object_or_404(Feedback, id=feedback_id)
            feedback.feedback_reply = reply
            feedback.reply_at = timezone.now()
            feedback.save()
            messages.success(request, "Reply sent successfully.")
            return redirect('admin_staff_feedback')  # Redirect to avoid form resubmission

    feedback_list = Feedback.objects.filter(sender_role='staff')
    context = {
        'feedback_list': feedback_list,
    }
    return render(request, "admin_templates/staff_feedback_template.html", context)