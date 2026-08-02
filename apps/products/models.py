from django.db import models
from django.core.validators import MinValueValidator

class Product(models.Model):
    """
    Product model representing items available for purchase.
    """
    name = models.CharField(
        max_length=200,
        help_text='Product display name'
    )
    description = models.TextField(
        blank=True,
        help_text='Detailed product description (optional)'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Product price'
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Available quantity in stock'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

    def is_in_stock(self, quantity):
        """Check if requested quantity is available."""
        return self.stock >= quantity

    def decrease_stock(self, quantity):
        """Decrease stock by specified quantity."""
        if self.is_in_stock(quantity):
            self.stock -= quantity
            self.save(update_fields=['stock', 'updated_at'])
            return True
        return False

    def increase_stock(self, quantity):
        """Increase stock by specified quantity."""
        self.stock += quantity
        self.save(update_fields=['stock', 'updated_at'])
        return True