from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    """
    subtotal = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'subtotal', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_subtotal(self, obj):
        """Calculate subtotal for the order item."""
        return obj.get_subtotal()


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    Includes nested OrderItem serialization.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_username', 'status', 'status_display',
            'total_amount', 'items', 'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_amount']
