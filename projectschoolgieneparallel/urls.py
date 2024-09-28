from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('studentapp.urls')),
    path('', include('staffapp.urls')),
    path('', include('adminapp.urls')),
    path('', include('chatapp.urls')),
    path('', include('paymentapp.urls')), 
    path('admin/', admin.site.urls),
   
]
