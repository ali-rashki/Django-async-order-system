from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product model.
    """
    # Fields to display in list view
    list_display = ['id', 'name', 'price', 'stock', 'created_at']

    # Fields to filter by
    list_filter = ['created_at', 'updated_at']

    # Fields to search
    search_fields = ['name', 'description']

    # Fields that are read-only
    readonly_fields = ['created_at', 'updated_at']

    # Fields to order by
    ordering = ['-created_at']

    # Fields to display in detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'stock')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
