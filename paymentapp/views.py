# views.py
import paypalrestsdk
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse
from .models import Fee, Payment
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm  
import uuid 
from reportlab.pdfgen import canvas
from django.http import JsonResponse, HttpResponse 
from io import BytesIO
from django.utils import timezone 
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os


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

def payment_success(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            payment_record = Payment.objects.get(payment_id=payment_id)
            payment_record.is_successful = True
            payment_record.save()

            fee = payment_record.fee
            fee.is_paid = True
            fee.save()

            # Generate and save the invoice immediately after successful payment
            download_invoice(request, payment_id)

            return render(request, 'payment_success.html', {'payment': payment_record})
        else:
            return redirect(reverse('payment_cancel'))

    except paypalrestsdk.ResourceNotFound as e:
        print(f"Payment not found: {str(e)}")
        return redirect(reverse('payment_cancel'))

# views.py
# def payment_success(request):
#     payment_id = request.GET.get('paymentId')
#     payer_id = request.GET.get('PayerID')

#     try:
#         # Retrieve the PayPal payment object using PayPal SDK
#         payment = paypalrestsdk.Payment.find(payment_id)
        
#         # Execute the payment if it exists and is valid
#         if payment.execute({"payer_id": payer_id}):
#             # Mark the payment as successful in your database
#             payment_record = Payment.objects.get(payment_id=payment_id)
#             payment_record.is_successful = True
#             payment_record.save()

#             # Mark the fee as paid
#             fee = payment_record.fee
#             fee.is_paid = True
#             fee.save()

#             return render(request, 'payment_success.html', {'payment': payment_record})
#         else:
#             return redirect(reverse('payment_cancel'))

#     except paypalrestsdk.ResourceNotFound as e:
#         # Handle the error if the payment ID isn't found in PayPal
#         print(f"Payment not found: {str(e)}")
#         return redirect(reverse('payment_cancel'))


def payment_cancel(request):
    return render(request, 'payment_failed.html')

# views.py
def payment_cancel(request):
    return render(request, 'payment_failed.html')



def generate_invoice(payment):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.textColor = colors.darkblue
    title_style.fontSize = 24
    normal_style = styles['Normal']

    # Add School Name at the top
    elements.append(Paragraph("Schoolgiene", title_style))
    elements.append(Spacer(1, 0.2 * inch))  # Add space below the school name
    
    # Add Invoice Title
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 0.1 * inch))  # Add space after title
    
    # Add Payment ID and Details
    elements.append(Paragraph(f"Payment ID: {payment.payment_id}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {payment.date.strftime('%Y-%m-%d')}", normal_style))
    elements.append(Spacer(1, 0.2 * inch))  # Add space before table
    
    # Add Payment details in a table
    data = [
        ["Student", payment.fee.student.username],
        ["Amount Paid", f"${payment.amount_paid}"],
        ["Fee Description", payment.fee.description or "N/A"],
    ]

    table = Table(data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(table)

    # Generate the PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer

def download_invoice(request, payment_id):
    payment = get_object_or_404(Payment, payment_id=payment_id)
    
    # Check if the invoice already exists
    if payment.invoice:
        # If it exists, serve the existing file
        return FileResponse(open(payment.invoice.path, 'rb'), as_attachment=True, filename=f"invoice_{payment.payment_id}.pdf")
    
    # If the invoice doesn't exist, generate it
    pdf_buffer = generate_invoice(payment)
    
    # Save the invoice to the file system
    invoice_filename = f"invoice_{payment.payment_id}.pdf"
    invoice_path = os.path.join(settings.MEDIA_ROOT, 'invoices', invoice_filename)
    
    # Create directories if not exist
    os.makedirs(os.path.dirname(invoice_path), exist_ok=True)
    
    with open(invoice_path, 'wb') as f:
        f.write(pdf_buffer.getbuffer())
    
    # Save the invoice path to the payment record
    payment.invoice = f'invoices/{invoice_filename}'
    payment.save()

    # Return the invoice as a response
    return FileResponse(open(invoice_path, 'rb'), as_attachment=True, filename=invoice_filename)