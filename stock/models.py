from django.db import models
from django.contrib.auth.models import  User

# Create your models here.

class Unit(models.Model):
    name=models.CharField(max_length=50)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class Category(models.Model):
    name = models.CharField(max_length=200)
    
    class Meta:
        verbose_name_plural = 'categories'
    def __str__(self) -> str:
        return self.name
    
    
    


class Purchase(models.Model):
    name = models.CharField(max_length=200)
    price_variation = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit=models.ForeignKey(Unit,on_delete=models.CASCADE,default='')
    quantity = models.DecimalField(max_digits=8, decimal_places=2,)
    status = models.CharField(max_length=100, default='pending')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    received_date = models.DateField(null=True, blank=True)
    cancelled_date=models.DateTimeField(null=True,blank=True)
    
    class Meta:
        permissions=[
            ('cancel_purchase', 'Can cancel purchase'),
            ('receive_purchase', 'Can receive purchase'),
            ('generate_report_purchase', 'Can generate report purchase'),
            ('view_stock', 'Can view stock')
        ]
        
    def __str__(self) -> str:
        return self.name    
        
class ClosingStock(models.Model):
    name=models.ForeignKey(Purchase, on_delete=models.CASCADE)
    quantity=models.DecimalField(max_digits=4,decimal_places=2)
    date=models.DateField()
    
    def __str__(self) -> str:
        return self.name.name
    
    
class Product(models.Model):
    name=models.ForeignKey(Purchase, on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=8,decimal_places=2)
        
    
class Wastage(models.Model):
    name=models.ForeignKey(Purchase, on_delete=models.CASCADE) 
    quantity=models.DecimalField(max_digits=5,decimal_places=2)
    date=models.DateField()   
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    
    

class Order(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.DecimalField(max_digits=4,decimal_places=2)
    date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True,)
    update_at=models.DateTimeField(auto_now=True,)
    status=models.CharField(max_length=50,default='pending')
    previous_status = models.CharField(max_length=20, default='pending')
    
    
    def save(self, *args, **kwargs):
        if self.pk:  # Check if it's an update
            old_order = Order.objects.get(pk=self.pk)
            self.previous_status = old_order.status
        super().save(*args, **kwargs)
        
        
class ToDoList(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activities_name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    date = models.DateField()
    time = models.TimeField(auto_now=False, auto_now_add=False)
    
    def __str__(self):
        return f"{self.user} - {self.activities_name} - {self.status}"







