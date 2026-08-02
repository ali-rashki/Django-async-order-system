from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import models
import logging
import os
from io import BytesIO
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id):
    """
    Task to send order confirmation email asynchronously.

    Args:
        order_id (int): ID of the order

    This task will retry up to 3 times if it fails.
    """
    from .models import Order

    try:
        # Get the order
        order = Order.objects.get(id=order_id)

        # Build email subject and message
        subject = f'Order Confirmation - Order #{order.id}'
        message = f"""
        Hello {order.user.username},

        Your order has been confirmed!

        Order ID: #{order.id}
        Total Amount: {order.total_amount}
        Status: {order.get_status_display()}

        Thank you for your purchase!
        """

        # Send email (for now, just log it)
        # In production, you would use:
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])

        # For development, log the email
        logger.info(f"📧 Email sent to {order.user.email} for Order #{order.id}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Message: {message}")

        return f"Email sent for Order #{order.id}"

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to send email for Order {order_id}: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds


@shared_task(bind=True, max_retries=3)
def generate_invoice_pdf(self, order_id):
    """
    Task to generate PDF invoice for an order.

    Args:
        order_id (int): ID of the order
    """
    from .models import Order
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    try:
        order = Order.objects.get(id=order_id)

        # Create PDF in memory
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(50, height - 50, "INVOICE")

        # Order details
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, height - 90, f"Order #{order.id}")

        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 115, f"User: {order.user.username}")
        pdf.drawString(50, height - 135, f"Status: {order.get_status_display()}")
        pdf.drawString(50, height - 155, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")

        # Divider line
        pdf.line(50, height - 170, width - 50, height - 170)

        # Items header
        y = height - 195
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Product")
        pdf.drawString(250, y, "Quantity")
        pdf.drawString(350, y, "Price")
        pdf.drawString(450, y, "Subtotal")

        # Divider line
        pdf.line(50, y - 10, width - 50, y - 10)

        # Items
        pdf.setFont("Helvetica", 12)
        y -= 30
        for item in order.items.all():
            pdf.drawString(50, y, item.product.name[:30])
            pdf.drawString(250, y, str(item.quantity))
            pdf.drawString(350, y, f"{item.price:,.0f}")
            pdf.drawString(450, y, f"{item.get_subtotal():,.0f}")
            y -= 25

        # Total
        y -= 20
        pdf.line(350, y + 10, width - 50, y + 10)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(350, y - 5, f"Total: {order.total_amount:,.0f}")

        # Footer
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 30, "Thank you for your purchase!")
        pdf.drawString(50, 15, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")

        pdf.save()

        # Save to file
        filename = f"invoices/order_{order.id}.pdf"
        os.makedirs("invoices", exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(buffer.getvalue())

        logger.info(f"📄 PDF Invoice generated for Order #{order.id}")
        logger.info(f"   Saved to: {filename}")

        return f"PDF Invoice generated for Order #{order.id}"

    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        raise
    except Exception as e:
        logger.error(f"Failed to generate PDF for Order {order_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def cancel_old_pending_orders():
    """
    Scheduled task to cancel pending orders older than 24 hours.
    Runs daily at 9:00 AM.
    """
    from .models import Order, OrderStatus

    # Calculate cutoff time (24 hours ago)
    cutoff_time = timezone.now() - timedelta(hours=24)

    # Find old pending orders
    old_orders = Order.objects.filter(
        status=OrderStatus.PENDING,
        created_at__lt=cutoff_time
    )

    count = old_orders.count()

    if count > 0:
        # Cancel them
        for order in old_orders:
            order.mark_as_cancelled()
            logger.info(f"🕐 Order #{order.id} cancelled due to timeout")

        logger.info(f"🕐 Cancelled {count} old pending orders")
    else:
        logger.info("🕐 No old pending orders to cancel")

    return f"Cancelled {count} old pending orders"


@shared_task
def cleanup_old_invoices():
    """
    Scheduled task to clean up old invoice files (older than 30 days).
    Runs every Sunday at midnight.
    """
    invoices_dir = "invoices"
    if not os.path.exists(invoices_dir):
        return "No invoices directory found"

    cutoff_time = datetime.now() - timedelta(days=30)
    deleted_count = 0

    for filename in os.listdir(invoices_dir):
        filepath = os.path.join(invoices_dir, filename)
        if os.path.isfile(filepath):
            # Get file modification time
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff_time:
                os.remove(filepath)
                deleted_count += 1
                logger.info(f"🗑️ Deleted old invoice: {filename}")

    logger.info(f"🗑️ Cleaned up {deleted_count} old invoice files")
    return f"Deleted {deleted_count} old invoice files"


@shared_task
def send_daily_sales_report():
    """
    Send daily sales report to admin.
    Runs every day at 6:00 PM.
    """
    from .models import Order, OrderStatus

    # Get today's orders
    today = timezone.now().date()
    today_orders = Order.objects.filter(
        created_at__date=today
    )

    total_orders = today_orders.count()
    total_amount = today_orders.aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0

    completed_count = today_orders.filter(status=OrderStatus.COMPLETED).count()
    pending_count = today_orders.filter(status=OrderStatus.PENDING).count()
    failed_count = today_orders.filter(status=OrderStatus.FAILED).count()
    cancelled_count = today_orders.filter(status=OrderStatus.CANCELLED).count()

    report = f"""
    📊 Daily Sales Report - {today}
    ================================
    Total Orders: {total_orders}
    Total Amount: {total_amount:,.0f}

    Status Breakdown:
    - Completed: {completed_count}
    - Pending: {pending_count}
    - Failed: {failed_count}
    - Cancelled: {cancelled_count}
    """

    logger.info(report)

    # In production, you would send this email to admin
    # send_mail(
    #     f'Daily Sales Report - {today}',
    #     report,
    #     settings.DEFAULT_FROM_EMAIL,
    #     ['admin@example.com']
    # )

    return f"Daily sales report sent for {today}"
