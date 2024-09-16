from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Purchase)
admin.site.register(Category)
admin.site.register(ClosingStock)
admin.site.register(Wastage)
admin.site.register(Order)
admin.site.register(ToDoList)