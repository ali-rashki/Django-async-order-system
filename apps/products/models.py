from django.db import models

class product(models.Model):
    Product_name = models.CharField(max_length=100)
    product_description = models.TextField(null=True, blank=True)
    price = models.DecimalField()
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


from django.db import models
from django.core.validators import MinValueValidator

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت"
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="موجودی"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_in_stock(self, quantity):
        """بررسی موجودی کافی"""
        return self.stock >= quantity

    def decrease_stock(self, quantity):
        """کاهش موجودی"""
        if self.is_in_stock(quantity):
            self.stock -= quantity
            self.save()
            return True
        return False