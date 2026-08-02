from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views import ProductViewSet
from apps.orders.views import OrderViewSet

# Create router
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
