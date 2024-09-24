from django.shortcuts import render,redirect,get_object_or_404,get_list_or_404
from django.views import View
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.models import User,Permission,Group
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.contrib import messages
import calendar
from collections import defaultdict
from stock.models import Purchase,Product,Order,Wastage,ToDoList
from django.db.models.functions import TruncMonth,TruncDay
from django.db.models import ExpressionWrapper,F,FloatField,Sum
import json
from rest_framework import status,generics
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated,AllowAny
import logging
from rest_framework.response import Response
from stock.serializers import  ProductSerializer,CustomTokenObtainPairSerializer,UserSerializer
from datetime import datetime, timedelta
from django.utils import  timezone
from decimal import Decimal
# Create your views here.

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def Dashboard(request):
        day_abbr = [calendar.day_abbr[i].upper() for i in range(0, 7)]
        month_abbr = [calendar.month_abbr[i].upper() for i in range(1, 13)]
        now = timezone.datetime.now()
        today=now.date()
        tomorrow=today + timedelta(days=1)
        
        yesterday=today - timedelta(days=1)

        # Initialize start_date and end_date
        start_date = today
        end_date = today

        if request.method == 'POST':
            # Get the filter date from POST request
            filter_date_str = request.POST.get('filter')
            
            if filter_date_str:
                try:
                    filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
                    
                    # Determine if the filter is for today or yesterday
                    if filter_date == today:
                        start_date = today
                        end_date = today
                    elif filter_date == yesterday:
                        start_date = yesterday
                        end_date = yesterday
                    else:
                        # Handle other date ranges if needed
                        start_date = filter_date
                        end_date = filter_date
                
                except ValueError:
                    # Handle invalid date format
                    pass
        
        start_of_week = today - timedelta(days=today.weekday()) 
        end_of_week = start_of_week + timedelta(days=6)

        start_of_last_week = start_of_week - timedelta(days=7)  
        end_of_last_week = start_of_week - timedelta(days=1) 
        
        total_user=User.objects.filter(is_staff=True).count() 
        
        yesterday_order=Order.objects.filter(status='charged',date=yesterday).count()
        
        today_order=Order.objects.filter(status='charged',date=today).count()
        
        if yesterday_order == 0:
            if today_order > 0:
                order_rate = 100
            else:
                order_rate = 0
        else:
            order_rate=((today_order - yesterday_order)/yesterday_order)*100
            
        
        total_order = Order.objects.filter(date__range=[start_date, end_date]).count()
        
        total_income=Order.objects.filter(status='charged',date__range=[start_date,end_date]).aggregate(
            total_order=Sum(ExpressionWrapper(F('quantity')*F('name__price'),output_field=FloatField())))['total_order'] or 0
        
        yesterday_income=Order.objects.filter(status='charged',date=yesterday).aggregate(
            total_order=Sum(ExpressionWrapper(F('quantity')*F('name__price'),output_field=FloatField())))['total_order'] or 0   
        
        today_income=Order.objects.filter(status='charged',date__range=[start_date,end_date]).aggregate(
            total_order=Sum(ExpressionWrapper(F('quantity')*F('name__price'),output_field=FloatField())))['total_order'] or 0
        
        
        
        if yesterday_income == 0:
            if today_income > 0:
                income_rate = today_income
            else:
                income_rate = 0
        else:
            income_rate=today_income-yesterday_income
            
            
        yesterday_purchase = Purchase.objects.filter(status='received',date=yesterday).aggregate(
            total_purchase=Sum(ExpressionWrapper(F('quantity') * F('price_variation'), output_field=FloatField()))
        )['total_purchase'] or 0
        
        today_purchase=Purchase.objects.filter(status='received',date=today).aggregate(
            total_purchase=Sum(ExpressionWrapper(F('quantity') * F('price_variation'), output_field=FloatField()))
        )['total_purchase'] or 0
        
        if yesterday_purchase == 0:
            if today_purchase :
                purchase_rate = today_purchase
            else:
                purchase_rate = 0
        else:
            purchase_rate= today_purchase - yesterday_purchase
            
        yesterday_wastage=Wastage.objects.filter(date=yesterday).aggregate(
            total_wastage=Sum(ExpressionWrapper(F('quantity'), output_field=FloatField()))
        )['total_wastage'] or 0
        
        today_wastage=Wastage.objects.filter(date=today).aggregate(
            total_wastage=Sum(ExpressionWrapper(F('quantity'), output_field=FloatField()))
        )['total_wastage'] or 0
        
        if yesterday_wastage == 0:
            if today_wastage > 0:
                wastage_rate = today_wastage
            else:
                wastage_rate = 0
        else:
            wastage_rate=today_wastage-yesterday_wastage
        
        monthly_purchase = Purchase.objects.filter(status='received',).annotate(
                month=TruncMonth('received_date',)
            ).values('month',).annotate(
                month_total=Sum(ExpressionWrapper(F('quantity') * F('price_variation'), output_field=FloatField()))
            )
            

        monthly_sales = Order.objects.filter(status='charged').annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            month_total=Sum(ExpressionWrapper(F('quantity') * F('name__price'), output_field=FloatField()))
        ).order_by('month')

        ps=Order.objects.filter(status='charged').annotate(month=TruncMonth('date')).aggregate(
            tps=Sum(ExpressionWrapper(F('quantity')*F('name__price'),output_field=FloatField())))['tps'] or 0
        
        
        sp=Purchase.objects.filter(status='received').annotate(month=TruncMonth('date')).aggregate(
            spt=(Sum(ExpressionWrapper(F('quantity')*F('price_variation'),output_field=FloatField()))))['spt'] or 0
        
        p=ps-sp
        
        day_wastage=Wastage.objects.filter(date__range=[start_date,end_date]).annotate(day=TruncDay('date')).aggregate(
            wast=Sum(ExpressionWrapper(F('quantity')*F('name__price_variation'),output_field=FloatField()))
        )['wast'] or 0
        
        
        
        purchases = Purchase.objects.filter(status='received',received_date__range=[start_date,end_date]).aggregate(
            total_purchase=Sum(ExpressionWrapper(F('quantity') * F('price_variation'), output_field=FloatField()))
        )['total_purchase'] or 0 
        
        day_purchases = Purchase.objects.filter(
            status='received',
            received_date__range=[start_of_last_week, end_of_week]
        ).annotate(day=TruncDay('received_date')).values('day').annotate(
            day_total=Sum(ExpressionWrapper(F('quantity') * F('price_variation'), output_field=FloatField()))
        ) 

        this_week_data = defaultdict(float) 
        last_week_data = defaultdict(float)

        for purchase in day_purchases:
            day = purchase['day']
            total = purchase['day_total']
            if start_of_week <= day <= end_of_week:
                day_index = (day - start_of_week).days
                this_week_data[day_abbr[day_index]] = total
            elif start_of_last_week <= day <= end_of_last_week:
                day_index = (day - start_of_last_week).days
                last_week_data[day_abbr[day_index]] = total

        # Prepare labels and datasets for Chart.js
        day_purchase = day_abbr
        this_week_totals = [this_week_data.get(day, 0) for day in day_purchase]
        last_week_totals = [last_week_data.get(day, 0) for day in day_purchase]

        # Aggregate monthly purchases

        purchases_totals = defaultdict(float)
        sales_totals = defaultdict(float)

        for item in monthly_purchase:
            month_index = item['month'].month - 1
            purchases_totals[month_abbr[month_index]] += item['month_total']

        for item in monthly_sales:
            month_index = item['month'].month - 1
            sales_totals[month_abbr[month_index]] += item['month_total']

        months = month_abbr
        purchase_totals_list = [purchases_totals[month] for month in months]
        sales_totals_list = [sales_totals[month] for month in months]
        
        ToDoList.objects.filter(date=today, status='Pending').update(status='In Progress')
        
        ToDoList.objects.filter(date=tomorrow, status='Pending').update(status='Due Tomorrow')
        
        ToDoList.objects.filter(date__lt=now, status='pending').update(status='Completed')
        
        todos=ToDoList.objects.filter(user=request.user).order_by('-date')
        
        products=Order.objects.filter(status='charged').values('name__name__category__name').annotate(total=Sum('quantity')).order_by('-total')[:5]
        
        products_list = list(products)
        
        orders=Order.objects.filter(status='charged').order_by('-date')
        
        

        
        context = {
            'purchase_rate':purchase_rate,
            'wastage_rate':wastage_rate,
            'order_rate':order_rate,
            'orders':orders,
            'products': json.dumps(products_list, cls=DecimalEncoder),
            'pd':todos,
            'purchase_totals': json.dumps(purchase_totals_list),
            'sales_totals': json.dumps(sales_totals_list),
            'months': json.dumps(months),
            'this_week_totals': json.dumps(this_week_totals),
            'last_week_totals': json.dumps(last_week_totals),
            'day_purchase': json.dumps(day_purchase),
            'time': now,
            'day': now.strftime('%A'),
            'second': now.second,
            'minute': now.minute,
            'hour': now.hour,
            'month': now.strftime('%B'),
            'year': now.year,
            'purchases': purchases,
            'total_user':total_user,
            'total_income':total_income,
            'p':p,
            'total_order':total_order,
            'day_wastage':day_wastage,
            'filter':start_date,
            'start_date':start_date,
            'end_date':end_date,
            'income_rate':income_rate,
        }
        return render(request, 'dashboard/home.html', context)


class UserManagement(PermissionRequiredMixin,LoginRequiredMixin, View):
    template_name = 'auth/users.html'
    permission_required=''

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            username = request.POST['username']
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            password = request.POST['password']
            confirm_password = request.POST['password']

            if password != confirm_password:
                messages.error(request, 'Passwords do not match')
                return self.get(request, *args, **kwargs)
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return self.get(request, *args, **kwargs)
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return self.get(request, *args, **kwargs)
            
            user=User.objects.create_user(username=username,first_name=first_name,last_name=last_name,email=email,password=password)
            user.save()
            messages.success(request, 'User created successfully')
            return redirect('users')
    
    
    def get(self, request, *args, **kwargs):
        groups=Group.objects.all()
        users = User.objects.all()
        now=timezone.datetime.now()

        context={
            'users':users,
            'groups':groups,
            'time':now,
            'day':now.strftime('%A'),
            'second':now.second,
            'minute':now.minute,
            'hour':now.hour,
            'month':now.strftime('%B'),
            'year':now.year
            }
        return render(request, self.template_name, context)

class UserUpdateDeleteView(PermissionRequiredMixin,LoginRequiredMixin,View):
    model=User
    template_name='auth/users.html'
    permission_required=''

    def post(self, request, id, *args, **kwargs):
        user=User.objects.get(id=id)
        if id:
            user.username=request.POST['username']
            user.first_name=request.POST['first_name']
            user.last_name=request.POST['last_name']
            user.email=request.POST['email']
            user.save()
            return redirect('users')
        return render (request, self.template_name)
    
    def get(self, request, id, *args, **kwargs):
        user=User.objects.get(id=id)
        user.delete()
        return redirect('users')
    


class RoleManagement(PermissionRequiredMixin,LoginRequiredMixin,View):
    template_name = 'auth/roles.html'
    permission_required=''
    
    
    def get(self, request, *args, **kwargs):
        groups = Group.objects.all()
        now=timezone.datetime.now()
        messages_data = [{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)
        context={
            'time':now,
            'day':now.strftime('%A'),
            'second':now.second,
            'minute':now.minute,
            'hour':now.hour,
            'month':now.strftime('%B'),
            'year':now.year,
            'groups':groups,
            'messages_json': messages_json
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            name=request.POST['name']
            Group.objects.get_or_create(name=name)
            messages.success(request, 'Role created successfully')
            return redirect('roles-management')
        
        
class UpdateDeleteRole(PermissionRequiredMixin,LoginRequiredMixin,View):
    template_name = 'auth/roles.html'
    permission_required=''
    
    
    def post(self, request, id, *args, **kwargs):
            name=request.POST['name']
            Group.objects.filter(id=id).update(name=name)
            messages.success(request, 'Role updated successfully')
            return redirect('roles-management')
            
            
    def get(self, request, id, *args, **kwargs):
        Group.objects.get(id=id).delete()
        return redirect('roles-management')   
    
    
class RolePermission(PermissionRequiredMixin,LoginRequiredMixin,View):
    template_name = 'auth/role-permission.html'
    permission_required=''
    
    def get(self, request, id,*args, **kwargs):
        permissions = Permission.objects.all()
        group=Group.objects.get(id=id)
        now=timezone.datetime.now()
        
        messages_data = [{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)
        context={
            'time':now,
            'day':now.strftime('%A'),
            'second':now.second,
            'minute':now.minute,
            'hour':now.hour,
            'month':now.strftime('%B'),
            'year':now.year,
            'permissions':permissions,
            'group':group,
            'messages_json': messages_json
        }        
        return render(request, self.template_name, context)
    
    def post(self, request, id, *args, **kwargs):
        group = Group.objects.get(id=id)
        permissions =request.POST.getlist('permission[]')
        
        group.permissions.clear()

        for permission in permissions:
            permission=Permission.objects.get(id=permission)
            group.permissions.add(permission)

        messages.success(request, 'Permissions updated successfully')
        return redirect('roles-management')
    
    
class UserRole(PermissionRequiredMixin, LoginRequiredMixin, View):
    template_name = 'auth/users.html'
    permission_required = ''
    
    def get(self, request,user_id, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)
        groups = Group.objects.all()
        now = timezone.datetime.now()
        
        messages_data = [{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)
        
        context = {
            'time': now,
            'day': now.strftime('%A'),
            'second': now.second,
            'minute': now.minute,
            'hour': now.hour,
            'month': now.strftime('%B'),
            'year': now.year,
            'user': user,
            'groups': groups,
            'messages_json': messages_json
        }        
        return render(request, self.template_name, context)
    
    def post(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(User, id=user_id)
        groups = request.POST.getlist('group') 
        
        user.groups.clear()
        
        for group in groups:
            group = Group.objects.get(id=group)
            user.groups.add(group)
        
        messages.success(request, 'Groups updated successfully')
        return redirect('users')


class TodoListManagement(PermissionRequiredMixin, LoginRequiredMixin, View):
    template_name = 'dashboard/home.html'
    permission_required=''
    
    def get(self, request, *args, **kwargs):
        todos=get_list_or_404(ToDoList, user=request.user)
        now=timezone.datetime.now()
        messages_data = [{'message': message.message, 'tags': message.tags} for message in messages.get_messages(request)]
        messages_json = json.dumps(messages_data)
        context = {
            'pd':todos,
            'messages_json': messages_json,
            'day': now.strftime('%A'),
            'second': now.second,
            'minute': now.minute,
            'hour': now.hour,
            'month': now.strftime('%B'),
            'year': now.year,
        }   
        return render(request, self.template_name,context)
    
    def post(self, request, *args, **kwargs):
        activities_name = request.POST.get('activities_name')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        user = request.user

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date() 
            time = datetime.strptime(time_str, '%H:%M').time()     
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
            return redirect('home')

        # Create the ToDoList instance
        ToDoList.objects.create(
            activities_name=activities_name,
            description=description,
            date=date,
            time=time,
            user=user
        )
        messages.success(request, 'Activity created successfully')
        return redirect('home')
    
class UpdateDeleteTodoList(View,PermissionRequiredMixin,LoginRequiredMixin):
    permission_required=''
    
    def post(self,request,id,*args,**kwargs):
        time=request.POST.get('time')
        date=request.POST.get('date')
        priority=request.POST.get('priority')
        ToDoList.objects.filter(id=id).update(time=time,date=date,priority=priority)
        messages.success(request, 'Activity updated successfully')   
        return redirect('home')
    
    def get(self,request,id,*args,**kwargs):
        ToDoList.objects.get(id=id).delete()
        messages.success(request, 'Activity deleted successfully')
        return redirect('home')


logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        logger.info('Login attempt with data: %s', request.data)
        logger.info('Token created: %s', response.data.get('access'))
        return response

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            response_data = {
                'user': serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            headers = self.get_success_headers(serializer.data)
            return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

