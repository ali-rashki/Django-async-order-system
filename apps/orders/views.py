from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Order, OrderItem, OrderStatus
from .serializers import OrderSerializer
from apps.products.models import Product
from .tasks import send_order_confirmation_email, generate_invoice_pdf  # ✅ اضافه شد


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order model.
    Provides CRUD operations for orders.
    """
    queryset = Order.objects.all().select_related('user').prefetch_related('items__product')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter orders by user.
        Staff users can see all orders.
        """
        queryset = super().get_queryset()

        # Staff can see all orders
        if self.request.user.is_staff:
            return queryset

        # Regular users can only see their own orders
        return queryset.filter(user=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new order with items.
        """
        data = request.data
        items_data = data.get('items', [])

        # Create order
        order = Order.objects.create(
            user=request.user,
            status=OrderStatus.PENDING
        )

        # Create order items
        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = item_data.get('quantity', 1)

            product = Product.objects.get(id=product_id)

            # Check stock availability
            if not product.is_in_stock(quantity):
                raise serializers.ValidationError(
                    f"Product '{product.name}' has insufficient stock."
                )

            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            # Decrease stock
            product.decrease_stock(quantity)

        # Update total amount
        order.update_total()

        # Send confirmation email asynchronously
        send_order_confirmation_email.delay(order.id)

        # ✅ Generate invoice PDF asynchronously
        generate_invoice_pdf.delay(order.id)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
