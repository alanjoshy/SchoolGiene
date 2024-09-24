# views.py
import paypalrestsdk
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Fee, Payment

# Configure the PayPal SDK
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # "sandbox" or "live"
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})


# views.py
def create_payment(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    if request.method == 'POST':
        # Create a PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": request.build_absolute_uri('/payment/success/'),  # Payment success URL
                "cancel_url": request.build_absolute_uri('/payment/cancel/')},  # Payment cancellation URL
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Fee Payment for {fee.student.username}",
                        "sku": "fee_payment",
                        "price": str(fee.amount),  # Use the amount field
                        "currency": "USD",
                        "quantity": 1}]},
                "amount": {
                    "total": str(fee.amount),  # Use the amount field
                    "currency": "USD"},
                "description": "Payment for student fee"}]})

        if payment.create():
            # Save the payment ID in the Payment model using the amount field
            payment_record = Payment.objects.create(fee=fee, payment_id=payment.id, amount_paid=fee.amount)  # Use the amount field
            payment_record.save()

            # Redirect to the PayPal approval page
            for link in payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            return JsonResponse({"error": "Error while creating PayPal payment"})

    return render(request, 'payment_form.html', {'fee': fee})



# views.py
def payment_success(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)
    
    if payment.execute({"payer_id": payer_id}):
        # Find the corresponding Payment record and mark it as successful
        payment_record = Payment.objects.get(payment_id=payment_id)
        payment_record.is_successful = True
        payment_record.save()

        # Mark the Fee as paid
        fee = payment_record.fee
        fee.is_paid = True
        fee.save()

        return render(request, 'payment_success.html', {'payment': payment_record})
    else:
        return render(request, 'payment_failed.html')

# views.py
def payment_cancel(request):
    return render(request, 'payment_cancel.html')
