from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem model.
    Displayed within Order admin page.
    """
    model = OrderItem
    extra = 1  # Number of empty forms to display
    readonly_fields = ['created_at']
    fields = ['product', 'quantity', 'price', 'get_subtotal', 'created_at']
    readonly_fields = ['get_subtotal', 'created_at']

    def get_subtotal(self, obj):
        """Display subtotal for each item."""
        return obj.get_subtotal()

    get_subtotal.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Order model.
    """
    # Fields to display in list view
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at', 'status_badge']

    # Fields to filter by
    list_filter = ['status', 'created_at', 'updated_at']

    # Fields to search
    search_fields = ['user__username', 'user__email', 'id']

    # Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'total_amount']

    # Fields to order by
    ordering = ['-created_at']

    # Inline items
    inlines = [OrderItemInline]

    # Fieldsets for detail view
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """
        Display status with color coding.
        """
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    # Custom actions for bulk operations
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed', 'mark_as_cancelled']

    def mark_as_processing(self, request, queryset):
        """Bulk action: Mark selected orders as processing."""
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} orders marked as processing.')

    mark_as_processing.short_description = 'Mark selected as Processing'

    def mark_as_completed(self, request, queryset):
        """Bulk action: Mark selected orders as completed."""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} orders marked as completed.')

    mark_as_completed.short_description = 'Mark selected as Completed'

    def mark_as_failed(self, request, queryset):
        """Bulk action: Mark selected orders as failed."""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} orders marked as failed.')

    mark_as_failed.short_description = 'Mark selected as Failed'

    def mark_as_cancelled(self, request, queryset):
        """Bulk action: Mark selected orders as cancelled."""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} orders marked as cancelled.')

    mark_as_cancelled.short_description = 'Mark selected as Cancelled'
