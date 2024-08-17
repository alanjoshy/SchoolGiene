from django.http import HttpResponse
from django.shortcuts import redirect, render , get_object_or_404
from django.contrib.auth import authenticate, login,logout
from adminapp.models import SchoolUser,Course,Subject
from django.contrib.auth.models import User, auth
from django.views.decorators.cache import cache_control
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required


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
    return render(request,'admin_templates/home.html')
    

# adminlogin 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    
    if request.method == 'GET': 
        if request.user.is_authenticated:
            if request.user.is_superuser:  
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'You do not have admin privileges.')
                logout(request)
                return redirect('admin_login')
        return render(request, 'admin_templates/admin_login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'admin_templates/admin_login.html')
        
        user = authenticate(username=username, password=password) 
        
        if user is not None:
            if user.is_superuser:  # Check if the user is a superuser
                login(request, user)
                messages.success(request, f'{username} logged in.')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'You do not have admin privileges.')
                return render(request, 'admin_templates/admin_login.html')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'admin_templates/admin_login.html')
    
    return render(request, 'admin_templates/admin_login.html')


# admin dashboard
@login_required(login_url='admin_login') 
def admin_dashboard(request):
    # students count
    student = SchoolUser.objects.filter(role='student')
    student_count = student.count() 
    
    # staff count
    staff = SchoolUser.objects.filter(role='staff')
    staff_count = staff.count() 
    
    
    # course count
    course = Course.objects.all()
    course_count = course.count()
    
     # subject count
    subject = Subject.objects.all()
    subject_count = subject.count()
    
    context = {
        'student_count': student_count, 
        'staff_count': staff_count, 
        'course_count' : course_count,
        'subject_count' : subject_count,
    }
    
    if not request.user.is_superuser:
        return redirect('admin_login')  # Redirect if the user is not a superuser
    return render(request, 'admin_templates/home_content.html',context)


# admin logout 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_logout(request):
    auth.logout(request)  
    messages.success(request, 'You have been logged out.')
    clear_all_cache()
    return render(request, 'admin_templates/admin_login.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_student(request):
    # Fetch all students
    student = SchoolUser.objects.filter(role='student') 
    # count students

    student_count = student.count() 
    
    context = {
        'students': student,
        'student_count': student_count, 
    }
    return render(request, 'admin_templates/manage_student_template.html',context)


# student approval
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def approve_student(request, student_id):
    student = get_object_or_404(SchoolUser, id=student_id)
    student.is_approved = True
    student.save()
    messages.success(request, 'Student has been approved.')
    return redirect('manage_student') 
        

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_staff(request):
    # Fetch all staff members
    staff = SchoolUser.objects.filter(role='staff') 
    # count staffs
    staff_count = staff.count()
    context = {
        'staff_members': staff,
        'staff_count' : staff_count,
        
    }
    return render(request,'admin_templates/manage_staff_template.html',context) 


def add_subject(request):
    return render(request, 'admin_templates/add_subject_template.html')


def add_student(request):
    return render(request, 'admin_templates/add_student_template.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_course(request):
    if request.method == 'POST':
        course_name = request.POST.get('course_name')
        # course_description = request.POST.get('description')

        # Create the course
        course = Course.objects.create(name=course_name)
        messages.success(request, f'{course_name} created..')

        # Optional: You can enroll students right after creating the course
        # # Assuming you have a list of student IDs you want to enroll
        # student_ids = request.POST.getlist('students')
        # students = SchoolUser.objects.filter(id__in=student_ids, role='student')
        
        # for student in students:
        #     course.enroll_student(student)

        # return redirect('course_list')  # Redirect to the course list page or any other page after creation

    return render(request, 'admin_templates/add_course_template.html')

# manage course
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses
    }  
    return render(request, 'admin_templates/manage_course_template.html', context)

# add subject
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def add_subject(request):
    if request.method == 'POST':
        # Retrieve data from the form
        subject_name = request.POST.get('subject_name')
        course_id = request.POST.get('course_id')
        staff_id = request.POST.get('staff_id')
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            messages.error(request, 'Selected course does not exist.')
            return redirect('add_subject')  # Redirect back to form       
        try:
            staff = SchoolUser.objects.get(id=staff_id)
        except SchoolUser.DoesNotExist:
            messages.error(request, 'Selected staff member does not exist.')
            return redirect('add_subject') 

        subject = Subject.objects.create(
            name=subject_name,
            course=course,
            staff_assigned=staff
        )
        
        messages.success(request, f'Subject "{subject_name}" created and assigned to {staff.username}.')
        return redirect('add_subject') 
    courses = Course.objects.all()
    staff_members = SchoolUser.objects.filter(role='staff')
    
    context = {
        'courses': courses,
        'staff_members': staff_members,
    }
    return render(request, 'admin_templates/add_subject_template.html', context)


# manage subjects
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def manage_subject(request):
    subjects = Subject.objects.select_related('course', 'staff_assigned').all()
    context = {
        'subjects': subjects,
    }
    return render(request, 'admin_templates/manage_subject_template.html',context)


# register student
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def register_student(request):
    if request.method == 'POST':
        # Extract data from the form
        first_name = request.POST.get('first_name') 
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        course_id = request.POST.get('course_id')
        profile_photo = request.FILES.get('profile_photo')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validate the data (add your own validation logic as needed)
        if not (first_name and last_name and username and email and phone and password1 and password2 and course_id):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('register_student')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('register_student')

        # Check if the username or email already exists
        if SchoolUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register_student')

        if SchoolUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('register_student')

        try:
            # Retrieve the selected course
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            messages.error(request, 'Selected course does not exist.')
            return redirect('register_student')

        # Create and save the student
        student = SchoolUser(
           first_name = first_name,
           last_name = last_name,
            username=username,
            email=email,
            phone=phone,
            address=address,
            profile_photo=profile_photo,
            role='student',
        )
        student.set_password(password1)  # Hash the password
        student.save()

        # Enroll the student in the selected course
        course.enroll_student(student)

        # Provide feedback to the user
        messages.success(request, f'Student {first_name} {last_name} with {username}has been registered and enrolled in {course.name}.')
        return redirect('register_student')  # Redirect to the student list or another page

    # If GET request, render the registration page
    courses = Course.objects.all()
    context = {
        'courses': courses,  
    } 

    return render(request, 'admin_templates/add_student_template.html',  context) 


