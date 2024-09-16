from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from .models import *
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db.models import Sum, ExpressionWrapper, Avg, F, FloatField, DecimalField
from django.db.models.functions import  Coalesce
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import json
from django.utils import timezone
from datetime import  timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import  ProductSerializer
from rest_framework import viewsets


# Create your views here.

class UnitManagement(View,PermissionRequiredMixin,LoginRequiredMixin):
    template_name='unit/management.html'
    permission_required='stock.view_unit'
    
    def get(self,request,*args,**kwargs):
        units=Unit.objects.all()
        now=datetime.datetime.now()
        context={
            'time':now,
            'year':now.year,
            'month':now.strftime('%B'),
            'day':now.strftime('%A'),
            'units':units,
        }
        return render(request, self.template_name,context)
    
    def post(self,request,*args,**kwargs):
        name=request.POST['name']
        Unit.objects.create(name=name)
        messages.success(request, 'unit added successfully')
        return redirect('unit-management')
    
class UpdateDeleteUnit(View,PermissionRequiredMixin,LoginRequiredMixin):
    def get(self,request,id,*args,**kwargs):
        Unit.objects.get(id=id).delete()   
        messages.success(request, 'unit deleted successfully')
        return redirect('unit-management')
        
    def post(self,request,id,*args,**kwargs):
        name=request.POST['name']
        Unit.objects.filter(id=id).update(name=name)  
        messages.success(request, 'unit updated successfully')  
        return redirect('unit-management') 
    

class CategoryManagement(PermissionRequiredMixin, LoginRequiredMixin, View):
    template_name = 'category/management.html'
    permission_required = 'stock.view_category'

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        now = datetime.datetime.now()

        # Serialize messages for the current request
        messages_data = [{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)

        context = {
            'categories': categories,
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
            'messages_json': messages_json
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        if name:
            Category.objects.get_or_create(name=name)
            messages.success(request, 'Category created successfully')
        else:
            messages.error(request, 'Category name is required')
        return redirect('category-management')


class UpdateDelete(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "stock.change_category"
    template_name="category/management.html"

    def post(self, request, id, *args, **kwargs):
        category = get_object_or_404(Category, id=id)
        if id:
            category.name = request.POST['name']
            category.save()
            messages.success(request, 'category updated successfully')
            return redirect('category-management')

    def get(self, request, id, *args, **kwargs):
        category = get_object_or_404(Category, id=id)
        category.delete()
        messages.success(request, 'category deleted successfully')
        return redirect('category-management')


class PurchaseItemManagement(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'purchase/management.html'
    permission_required = 'stock.view_purchase'

    def get(self, request, *args, **kwargs):
        units=get_list_or_404(Unit)
        categories = get_list_or_404(Category)
        purchases = Purchase.objects.all().order_by('date')
        now = datetime.datetime.now()

        messages_data=[{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)
        
        context = {
            'units':units,
            'categories': categories,
            'purchases': purchases,
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
            'messages_json': messages_json
            
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        name = request.POST['name']
        unit=request.POST['unit']
        category = request.POST['category']
        price_variation = request.POST['price_variation']
        quantity = request.POST['quantity']
        date = request.POST['date']

        unit=Unit.objects.get(id=unit)
        category = Category.objects.get(id=category)
        Purchase.objects.create(
        name=name, unit=unit, category=category, price_variation=price_variation, quantity=quantity, date=date)
        messages.success(request, 'purchase order created successfully')
        return redirect('pending-purchase')


class UpdateDeletePurchase(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stock.change_purchase'
    template_name = 'purchase/management.html'

    def post(self, request, id, *args, **kwargs):
        name=request.POST['name']
        unit_id=request.POST['unit']
        category_id=request.POST['category']
        price_variation=request.POST['price_variation']
        quantity=request.POST['quantity']
        date=request.POST['date']
        
        unit=Unit.objects.get(id=unit_id)
        category=Category.objects.get(id=category_id)
        Purchase.objects.filter(id=id).update(name=name,unit=unit,category=category,price_variation=price_variation,quantity=quantity,date=date)
        messages.success(request, 'purchase order updated successfully')
        return redirect('pending-purchase')

    def get(self, request, id, *args, **kwargs):
        purchase = get_object_or_404(Purchase, id=id)
        purchase.delete()
        messages.info(request, "purchase order deleted successfully")
        return redirect('pending-purchase')


class ReceivedView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stock.receive_purchase'

    def get(self, request, id):
        purchase = get_object_or_404(Purchase, id=id)
        if purchase.status != 'received':
            purchase.status = 'received'
            purchase.received_date = datetime.datetime.now()
            purchase.save()
            messages.success(request, 'purchase order received successfully')
        return redirect('purchase-management')


class CancelledView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stock.cancel_purchase'

    def get(self, request, id):
        purchase = get_object_or_404(Purchase, id=id)
        if purchase.status != 'cancelled':
            purchase.status = 'cancelled'
            purchase.cancelled_date = datetime.datetime.now()
            purchase.save()
            messages.info(request, 'purchase order cancelled successfully')
        return redirect('purchase-management')


class Pending(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'purchase/pending.html'
    permission_required = 'stock.view_purchase'

    def get(self, request, *args, **kwargs):
        purchases = Purchase.objects.filter(status='pending')
        units=Unit.objects.all()
        categories=Category.objects.all()
        now = datetime.datetime.now()
        context={
            'purchases': purchases,
            'units':units,
            'categories':categories,
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
        }
        return render(request, self.template_name, context)


class Received(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stock.receive_purchase'
    template_name = 'purchase/received.html'

    def get(self, request, *args, **kwargs):
        purchases = Purchase.objects.filter(status='received')

        now = datetime.datetime.now()

        context = {
            'purchases': purchases,
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
        }
        return render(request, self.template_name, context)


class Cancelled(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'stock.receive_purchase'
    template_name = 'purchase/cancelled.html'

    def get(self, request, *args, **kwargs):
        purchases = Purchase.objects.filter(status='cancelled')
        now = datetime.datetime.now()

        context = {
            'purchases': purchases,
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
        }
        return render(request, self.template_name, context)
    
class deleteAll(View,LoginRequiredMixin,PermissionRequiredMixin):
    permission_required=''
    def get(self,request,*args,**kwargs):
        Purchase.objects.filter(status='pending').delete()
        return redirect('purchase-management')    


def purchase_report_pdf(request):
    # Fetch data from your model
    purchases = Purchase.objects.all()

    # Define the context
    context = {
        'purchases': purchases
    }

    # Render the HTML template with the context
    template = render_to_string('purchase/report.html', context)

    # Create the HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment;filename="purchase_report.pdf"'

    # Convert HTML to PDF
    result = pisa.CreatePDF(template, dest=response)

    # Check if there were errors
    if result.err:
        return HttpResponse(
            'We had some errors <pre>' + str(result.err) + '</pre>')

    return response


class StockItems(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = Purchase
    permission_required = 'stock.view_stock'
    template_name = 'stock/items.html'

    def get(self, request, *args, **kwargs):
        now = timezone.datetime.now()
        today = now.date()

        item_names = Purchase.objects.filter(status='received').values_list('name', flat=True).distinct()

        data = []

        for item_name in item_names:
            # Calculate waste and order quantities for today
            waste_quantity = Wastage.objects.filter(date=today, name__name=item_name).aggregate(Sum('quantity'))
            waste_quantity = waste_quantity['quantity__sum'] or 0

            order_quantity = Order.objects.filter(date=today, name__name__name=item_name).aggregate(Sum('quantity'))
            order_quantity = order_quantity['quantity__sum'] or 0

            purchase_quantity = Purchase.objects.filter(received_date=today, name=item_name).aggregate(Sum('quantity'))
            purchase_quantity = purchase_quantity['quantity__sum'] or 0

            last_closing_stock = ClosingStock.objects.filter(name__name=item_name).exclude(quantity=0).order_by('-date').first()
            opening_quantity = last_closing_stock.quantity if last_closing_stock else 0

            total_quantity = opening_quantity + purchase_quantity
            remain_quantity = total_quantity - (order_quantity + waste_quantity)

            closing_stock, created = ClosingStock.objects.update_or_create(
                date=today,
                name=Purchase.objects.filter(name=item_name).first(),  
                defaults={'quantity': remain_quantity}
            )
            data.append({
                'item_name': item_name,
                'purchase_quantity': purchase_quantity,
                'opening_quantity': opening_quantity,
                'closing_quantity': closing_stock.quantity,
                'total_quantity': total_quantity,
                'date': today,
                'order_quantity': order_quantity,
                'waste_quantity': waste_quantity
            })

        context = {
            'data': data,
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
        }
        return render(request, self.template_name, context)

    
    
    
class ProductManagement(View,LoginRequiredMixin,PermissionRequiredMixin):
    template_name='Product/management.html'
    permission_required=''
    
    def get (self,request,*args,**kwargs):
        products=Product.objects.all()
        purchases=Purchase.objects.all()
        now=datetime.datetime.now()
        messages_data=[{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)
        
        
        context={
            'products':products,
            'purchases':purchases,
            'time':now,
            'day':now.strftime('%A'),
            'month':now.strftime('%B'),
            'year':now.year,
            'messages_json':messages_json
        }
        
        return render(request, self.template_name,context)
    
    def post(self,request,*args,**kwargs):
        name_id=request.POST['name']
        price=request.POST['price']
        
        purchase=get_object_or_404(Purchase, id=name_id)
        
        if Product.objects.filter(name=purchase).exists():
            messages.info(request,'product already exists')
        else:
            
            Product.objects.get_or_create(name=purchase,price=price)
            messages.success(request,'product created successfully')
        return redirect('product-management')
    
    
class UpdateDeleteProduct(View,LoginRequiredMixin,PermissionRequiredMixin):
    permission_required=''
    
    
    def post(self,request,id,*args,**kwargs):
        price=request.POST['price']
        Product.objects.filter(id=id).update(price=price)  
        messages.success(request,'product updated successfully')  
        return redirect('product-management')  
    
    
    def get(self,request,id,*args,**kwargs):
        Product.objects.get(id=id).delete()
        messages.success(request,'product deleted successfully')   
        return redirect('product-management')
        
    
    
class OrderManagement(View,LoginRequiredMixin,PermissionRequiredMixin):
    template_name='Order/management.html'  
    permission_required=''
    
    def get(self,request,*args,**kwargs):
        orders=Order.objects.all().order_by('created_at')
        users=User.objects.all()
        products = Product.objects.all()
        now=datetime.datetime.now()
        messages_data=[{'message':messages.message, 'tags':messages.tags}for messages in messages.get_messages(request)]
        messages_json=json.dumps(messages_data)
        
        context={
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
            'orders':orders,
            'users':users,
            'products':products,
            'messages_json':messages_json
        }
        return render(request, self.template_name,context)
    
    def post(self,request,*args,**kwargs):
        user=request.POST['user']
        name_id=request.POST['name']
        quantity=request.POST['quantity']
        date=datetime.datetime.now()
        
        user=get_object_or_404(User, id=user)
        product=get_object_or_404(Product, id=name_id)
        
        Order.objects.create(user=user,name=product,quantity=quantity,date=date)
        messages.success(request,'order created successfully')
        return redirect('order-management')
    


class UpdateDeleteOrder(View,LoginRequiredMixin,PermissionRequiredMixin):
    permission_required=''
    
    def get(self,request,id,*args,**kwargs):
        Order.objects.get(id=id).delete()
        messages.success(request,'order deleted successfully')
        return redirect('order-management')
    
    def post(self,request,id,*args,**kwargs):
        quantity=request.POST['quantity']
        Order.objects.filter(id=id).update(quantity=quantity)
        messages.success(request, 'order updated successfully')
        return redirect('order-management')
    
class UserOrderManagement(View,PermissionRequiredMixin,LoginRequiredMixin):
    template_name='Order/user_order_management.html'
    permission_required='stock.view_purchase'
    
    def get(self,request,*args,**kwargs):
        user_order=Order.objects.filter(user=request.user)
        now=datetime.datetime.now()
        context={
            'time': now,
            'year': now.year,
            'month': now.strftime('%B'),
            'day': now.strftime('%A'),
            'user_order':user_order,
            }
        return render(request, self.template_name, context)
    
    def post(self,request,*args,**kwargs):
        name_id=request.POST['name']
        quantity=request.POST['quantity']
        date=datetime.datetime.now()
        user=request.user
        
        product=get_object_or_404(Product, id=name_id)
        
        Order.objects.create(name=product,user=user,quantity=quantity,date=date)
        messages.success(request, 'order crested successfully')
        return redirect('user-order-management')
        


class ChargedOrder(View,LoginRequiredMixin,PermissionRequiredMixin):
     def get(self, request, id, *args, **kwargs):
        try:
            order = Order.objects.get(id=id)
            if order.status != 'charged':
                order.status = 'charged'
                order.save()  
                messages.success(request, 'Order marked as charged successfully')
        except Order.DoesNotExist:
            messages.error(request, 'Order not found')
        return redirect('order-management')
        
class VoidedOrder(View,LoginRequiredMixin,PermissionRequiredMixin):
    def get(self,request,id,*args,**kwargs):
        try:
            order=Order.objects.get(id=id)
            if order.status != 'voided':
                order.status = 'voided'
                order.save()   
                messages.success(request, 'order voided successfully')
        except Order.DoesNotExist:
            messages.error(request, 'order not found')
        return redirect ('order-management')   
        
        

class wastageManagement(View,LoginRequiredMixin,PermissionRequiredMixin):
    template_name='wastage/management.html'
    permission_required=''
    
    def get(self,request,*args,**kwargs):
        wastages=Wastage.objects.all()
        purchases=Purchase.objects.filter(status='received')
        now=datetime.datetime.now()
        
        messages_data=[{'message':messages.message, 'tags':messages.tags} for messages in messages.get_messages(request)]
        messages_json=json.dumps(messages_data)
        
        context={
            'time':now,
            'wastages':wastages,
            'purchases':purchases,
            'messages_json':messages_json,
            'month':now.strftime('%B'),
            'day':now.strftime('%A'),
            'year':now.year
        }
        return render(request,self.template_name,context)
    
    
    def post(self,request,*args,**kwargs):
        name_id=request.POST['name']
        quantity=request.POST['quantity']
        date=datetime.datetime.now()
        
        purchase=get_object_or_404(Purchase,id=name_id)
        Wastage.objects.create(name=purchase,quantity=quantity,date=date)
        messages.success(request,'wastage product created successfully')
        return redirect('wastage-management')


class deleteUpdateWastage(View,LoginRequiredMixin,PermissionRequiredMixin):
    permission_required=''
    
    def get(self,request,id,*args,**kwargs):
        Wastage.objects.get(id=id).delete()
        messages.success(request,'wastage product deleted successfully')
        return redirect('wastage-management')
    
    
    def post(self,request,id,*args,**kwargs):
        quantity=request.POST['quantity']
        Wastage.objects.filter(id=id).update(quantity=quantity)
        messages.success(request,'wastage product updated successfully')
        return redirect('wastage-management')



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer