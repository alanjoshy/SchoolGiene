from django.urls import path,include
from . import views
from studentapp.views import  fee_section
urlpatterns = [
    path('create_payment/<int:fee_id>/', views.create_payment, name='create_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('fee_section/', fee_section, name='fee_section'),
    path('invoice/<str:payment_id>/', views.download_invoice, name='download_invoice'),
    path('download_invoice/<str:payment_id>/', views.download_invoice, name='download_invoice'),
]
