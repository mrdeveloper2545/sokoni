from django.urls import path
from .views import *
from . import views



urlpatterns = [
    path('dashboard/home', views.Dashboard, name='home'),
    path('', views.login_view, name='login'),
    path('logout/',views.logout_view, name="logout"),

    # userManagement
    path('user/', UserManagement.as_view(), name='users'),
    path('register/user', UserManagement.as_view(), name='register'),
    path('edit/user/<int:id>', UserUpdateDeleteView.as_view(), name='update-user'),
    path('view/user/<int:id>',UserUpdateDeleteView.as_view(), name="view-user"),
    path('delete/user/<int:id>',UserUpdateDeleteView.as_view(), name="delete-user"),
    
    # RolesManagement
    path('roles/', RoleManagement.as_view(), name='roles-management'),
    path('update/role/<int:id>', UpdateDeleteRole.as_view(), name='update-role'),
    path('delete/role/<int:id>', UpdateDeleteRole.as_view(), name='delete-role'),
    
    # RolesPermission
    path('role/permission/<int:id>', RolePermission.as_view(), name='role-permission'),
    path('user/role/<int:user_id>/', UserRole.as_view(), name='user-role'),
    
    
    # TodoListManagement
    path('todo/', TodoListManagement.as_view(), name='todo-list-management'),


]