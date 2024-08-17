from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login,logout 
from django.contrib import messages
from django.contrib.auth.models import User, auth
from adminapp.models import SchoolUser,Subject
from staffapp.models import Attendance,get_attendance_statistics
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required

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
    subjects_enrolled = Subject.objects.filter(students=student).count()
    attendance_stats = get_attendance_statistics(student)
    return render(request, "student_home_template.html", {
        "attendance_stats": attendance_stats,
        "subjects_enrolled": subjects_enrolled,
    })


# student register
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def student_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('lastname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        photo = request.FILES.get('photo')  # Handle file upload
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('staff_register')

        if SchoolUser.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('staff_register')

        if SchoolUser.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect('staff_register')

        # Create the user
        user = SchoolUser.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password1,
            phone=phone,
            profile_photo=photo,
            address = address,
        )

        # Ensure that the role is set to 'staff'
        user.role = 'student'
        user.save()

        messages.success(request, "Student registered successfully.")
        return redirect('admin_dashboard')  
    return render(request, 'student_register.html')

# cache 
def clear_all_cache():
    cache.clear() 
    
    
# logout
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def student_logout(request):
    auth.logout(request)  
    messages.success(request, 'You have been logged out.')
    clear_all_cache()
    return render(request, 'student_login.html') 
 