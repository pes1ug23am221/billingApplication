from django.db import models
from django.conf import settings


class Transaction(models.Model):
    STATUS_REVIEW = 'review'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CHOICES = [
        (STATUS_REVIEW, 'Review'),
        (STATUS_CONFIRMED, 'Confirmed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    PAYMENT_CASH = 'cash'
    PAYMENT_UPI = 'upi'
    PAYMENT_CARD = 'card'
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_UPI, 'UPI / QR'),
        (PAYMENT_CARD, 'Card'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REVIEW)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    customer_phone = models.CharField(max_length=20, blank=True, help_text='Customer WhatsApp or phone number')
    remarks = models.TextField(blank=True, help_text='Overall remarks from the vision service')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    store_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True, help_text='User notes')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bill #{self.pk} — {self.user.username} — ₹{self.total_amount} ({self.status})"


class TransactionImage(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='transaction_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Bill #{self.transaction_id}"


class TransactionItem(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    remark = models.CharField(max_length=300, blank=True, help_text='Per-item remark from vision service')

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} × {self.quantity} @ ₹{self.unit_price}"
