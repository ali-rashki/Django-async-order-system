from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.products.models import Product

User = get_user_model()


class OrderStatus(models.TextChoices):
    """
    Status choices for Order model lifecycle.
    Represents the state machine of an order from creation to completion.
    """
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'


class Order(models.Model):
    """
    Main Order model representing a customer purchase.

    This model tracks the entire lifecycle of an order including:
    - User who placed the order
    - Current status (state machine)
    - Total amount (calculated from items)
    - Timestamps for tracking
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        help_text='User who placed the order'
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        help_text='Current order status in the state machine'
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total order amount calculated from all items'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Order creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when order was successfully processed'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'Order #{self.id} - {self.user.username}'

    def update_total(self):
        from django.db.models import Sum, F

        total = self.items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0

        self.total_amount = total
        self.save(update_fields=['total_amount', 'updated_at'])
        return total

    def can_process(self):
        return self.status == OrderStatus.PENDING

    def mark_as_processing(self):
        if self.can_process():
            self.status = OrderStatus.PROCESSING
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False

    def mark_as_completed(self):
        self.status = OrderStatus.COMPLETED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at', 'updated_at'])

    def mark_as_failed(self):
        self.status = OrderStatus.FAILED
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_cancelled(self):
        self.status = OrderStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])


class OrderItem(models.Model):
    """
    Individual items within an order.

    Each item references a product with quantity and price at order time.
    Price is stored as a snapshot to preserve historical value.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Order this item belongs to'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        help_text='Product being ordered'
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Quantity ordered'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Unit price at order time (snapshot)'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Creation timestamp'
    )

    class Meta:
        unique_together = [['order', 'product']]
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_subtotal(self):
        return self.quantity * self.price

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)
