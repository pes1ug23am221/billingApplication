from django.contrib import admin
from .models import Transaction, TransactionImage, TransactionItem


class TransactionImageInline(admin.TabularInline):
    model = TransactionImage
    extra = 0
    readonly_fields = ['image', 'uploaded_at']


class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0
    fields = ['product_name', 'quantity', 'unit_price', 'total_price', 'remark']
    readonly_fields = ['total_price']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'store_name', 'created_at', 'confirmed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'store_name', 'remarks']
    readonly_fields = ['created_at', 'confirmed_at']
    inlines = [TransactionImageInline, TransactionItemInline]
