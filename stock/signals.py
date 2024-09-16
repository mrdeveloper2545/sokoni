from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from .models import *
from datetime import timedelta
from django.utils import timezone

@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, created, **kwargs):
    if created:
        # Handle order creation email
        subject = 'Order Confirmation'
        
    elif instance.status == 'charged' and instance.previous_status != 'charged':
        # Handle status change to "charged"
        subject = 'Order Charged'
    
    elif instance.status == 'voided' and instance.previous_status != 'voided':
        subject = 'Order Cancelled'    

    try:
        # Ensure `quantity` is an integer
        quantity = int(instance.quantity)
        
        # Ensure `price` is a Decimal
        price = Decimal(instance.name.price)
        
        # Calculate total price
        total_price = quantity * price
        
        # Construct the email message
        message = f'''
        Dear {instance.user.username},

        Your order for {instance.name.name} has been "{instance.status}".

        Quantity: {quantity}
        Date: {instance.date}
        Status: {instance.status}
        Price per unit: {price}
        Total: {total_price}

        Thank you for your purchase!

        Best regards,
        SMELL ME PERFUMES
        '''
        
        recipient_list = [instance.user.email]
        
        # Send the email
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    
    except ValueError as e:
        # Handle the case where conversion fails
        print(f"Error in value conversion: {e}")
    except Exception as e:
        # Handle other exceptions
        print(f"Error sending email: {e}")
        

@receiver(post_save, sender=ToDoList)
def status_in_progress(sender, instance, **kwargs):
    now = timezone.datetime.now().date()
    
    if now < instance.date and instance.status == 'pending':
        instance.status = 'In Progress' 
        instance.save(update_fields=['status']) 
        
@receiver(post_save, sender=ToDoList)
def update_status_due_tomorrow(sender, instance, **kwargs):
    now = timezone.datetime.now().date()
    tomorrow = now + timedelta(days=1)
    
    if instance.date == tomorrow and instance.status == 'pending':
        instance.status = 'Due Tomorrow'
        instance.save(update_fields=['status'])    
        
@receiver(post_save, sender=ToDoList)
def update_status_completed(sender, instance, **kwargs):
    now = timezone.datetime.now().date()
    
    if instance.date < now and instance.status == 'pending':
        instance.status = 'Completed'
        instance.save(update_fields=['status'])
        
        
