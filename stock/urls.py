from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'product', ProductViewSet)

urlpatterns = [
    # API routes
    
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # UnitManagement
    path('unit/', UnitManagement.as_view(), name="unit-management"),
    path('update/unit/<int:id>', UpdateDeleteUnit.as_view(), name="update-unit"),
    path('delete/unit/<int:id>', UpdateDeleteUnit.as_view(), name="delete-unit"),

    # CategoryManagement
    path('category/', CategoryManagement.as_view(), name="category-management"),
    path('update/category/<int:id>', UpdateDelete.as_view(), name="update-category"),
    path('delete/category/<int:id>', UpdateDelete.as_view(), name="delete-category"),

    # PurchaseManagement
    path('purchase/', PurchaseItemManagement.as_view(), name="purchase-management"),
    path('update/purchase/<int:id>', UpdateDeletePurchase.as_view(), name="update-purchase"),
    path('delete/purchase/<int:id>', UpdateDeletePurchase.as_view(), name="delete-purchase"),
    path('receive/purchase/<int:id>', ReceivedView.as_view(), name="received-purchase"),
    path('cancel/purchase/<int:id>', CancelledView.as_view(), name="cancelled-purchase"),
    path('pending/purchase', Pending.as_view(), name="pending-purchase"),
    path('received/purchase', Received.as_view(), name="purchase-received"),
    path('cancelled/purchase', Cancelled.as_view(), name="cancelled-purchase"),
    path('delete/purchase/all', deleteAll.as_view(), name='purchase-all'),

    # StockManagement
    path('stock/', StockItems.as_view(), name="stock-management"),
    path('purchase-report/pdf/', views.purchase_report_pdf, name='purchase-repo'),

    path('products/', ProductManagement.as_view(), name="product-management"),
    path('update/product/<int:id>/', UpdateDeleteProduct.as_view(), name="update-product"),
    path('delete/product/<int:id>/', UpdateDeleteProduct.as_view(), name="delete-product"),

    # OrderManagement
    path('order/', OrderManagement.as_view(), name="order-management"),
    path('update/order/<int:id>/', UpdateDeleteOrder.as_view(), name="update-order"),
    path('delete/order/<int:id>', UpdateDeleteOrder.as_view(), name="delete-order"),
    path('order/status/charge/<int:id>', ChargedOrder.as_view(), name="charged-order"),
    path('order/status/void/<int:id>', VoidedOrder.as_view(), name="voided-order"),

    # UserOrderManagement
    path('user-order/', UserOrderManagement.as_view(), name="users-order-management"),

    # WastageManagement
    path('wastages/', wastageManagement.as_view(), name="wastage-management"),
    path('delete/wastage/<int:id>/', deleteUpdateWastage.as_view(), name="delete-wastage"),
    path('update/wastage/<int:id>/', deleteUpdateWastage.as_view(), name="update-wastage"),


]
