from decimal import Decimal
from datetime import timedelta
import urllib.parse

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import Transaction, TransactionImage, TransactionItem
from .services.vision_service import process_images
from .services.upi_service import generate_upi_qr_base64, get_upi_payload

User = get_user_model()


@login_required
def dashboard_view(request):
    """
    Synchronized Shop Analytics & Control Center.
    Reflects the single store's central database: all cashiers and admin
    see synchronized sales numbers, pending review queues, and top items.
    """
    now = timezone.now()
    shop_txns = Transaction.objects.all()

    # Confirmed metrics across the store
    confirmed_txns = shop_txns.filter(status=Transaction.STATUS_CONFIRMED)
    confirmed_count = confirmed_txns.count()
    total_sales = confirmed_txns.aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    # Today's store sales
    today_sales = confirmed_txns.filter(
        created_at__date=now.date()
    ).aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    # This month store sales
    this_month_sales = confirmed_txns.filter(
        created_at__year=now.year,
        created_at__month=now.month
    ).aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    # This week store sales
    start_of_week = now.date() - timedelta(days=now.weekday())
    this_week_sales = confirmed_txns.filter(
        created_at__date__gte=start_of_week
    ).aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    # Synchronized pending review queue across all cashiers
    pending_bills = shop_txns.filter(
        status=Transaction.STATUS_REVIEW
    ).select_related('user').order_by('-created_at')
    pending_count = pending_bills.count()

    # Top 5 best-selling grocery products in the shop
    top_products = TransactionItem.objects.filter(
        transaction__status=Transaction.STATUS_CONFIRMED
    ).values('product_name').annotate(
        total_qty=Sum('quantity'),
        total_spend=Sum('total_price')
    ).order_by('-total_spend')[:5]

    # Active cashiers count
    active_cashiers_count = User.objects.filter(is_active=True).count()

    context = {
        'total_sales': total_sales,
        'today_sales': today_sales,
        'this_month_sales': this_month_sales,
        'this_week_sales': this_week_sales,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'pending_bills': pending_bills,
        'top_products': top_products,
        'active_cashiers_count': active_cashiers_count,
    }
    return render(request, 'billing/dashboard.html', context)


@login_required
def history_view(request):
    """
    Dedicated Shop Ledger: search, filter, and audit past bills across all cashiers.
    """
    txns = Transaction.objects.select_related('user').all()

    # 1. Search query (notes, product name, or bill ID)
    q = request.GET.get('q', '').strip()
    if q:
        txns = txns.filter(
            Q(notes__icontains=q) |
            Q(items__product_name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(id__iexact=q if q.isdigit() else None)
        ).distinct()

    # 2. Filter by status
    status = request.GET.get('status', '').strip()
    if status in [Transaction.STATUS_CONFIRMED, Transaction.STATUS_REVIEW]:
        txns = txns.filter(status=status)

    # 3. Filter by Cashier / Staff member
    cashier = request.GET.get('cashier', '').strip()
    if cashier:
        txns = txns.filter(user__username__iexact=cashier)

    # 4. Filter by date timeframe
    date_filter = request.GET.get('date_filter', '').strip()
    now = timezone.now()
    if date_filter == 'today':
        txns = txns.filter(created_at__date=now.date())
    elif date_filter == 'this_week':
        start_of_week = now.date() - timedelta(days=now.weekday())
        txns = txns.filter(created_at__date__gte=start_of_week)
    elif date_filter == 'this_month':
        txns = txns.filter(created_at__year=now.year, created_at__month=now.month)

    # Filter summary
    filtered_count = txns.count()
    filtered_total = txns.filter(status=Transaction.STATUS_CONFIRMED).aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')

    # All cashiers for filter dropdown
    available_cashiers = User.objects.filter(is_active=True).order_by('username')

    context = {
        'transactions': txns.order_by('-created_at'),
        'filtered_count': filtered_count,
        'filtered_total': filtered_total,
        'available_cashiers': available_cashiers,
        'current_q': q,
        'current_status': status,
        'current_cashier': cashier,
        'current_date_filter': date_filter,
    }
    return render(request, 'billing/history.html', context)


@login_required
def new_bill_view(request):
    """
    Handles camera photo uploads and calls the vision model service.
    Designed for concurrent execution across multiple cashier devices.
    """
    if request.method == 'GET':
        return render(request, 'billing/new_bill.html')

    # POST: upload images → call vision service → save → redirect to review
    images = request.FILES.getlist('images')
    if not images:
        messages.error(request, 'Please select at least one photo.')
        return render(request, 'billing/new_bill.html')

    # 1. Create transaction row for this cashier in central DB
    with transaction.atomic():
        txn = Transaction.objects.create(
            user=request.user,
            store_name='Main Counter',
        )

        # 2. Save uploaded images
        saved_paths = []
        for img in images:
            ti = TransactionImage.objects.create(transaction=txn, image=img)
            saved_paths.append(ti.image.path)

    # 3. Call model vision service (handles concurrent calls via FastAPI async)
    try:
        result = process_images(saved_paths)
    except Exception as exc:
        txn.delete()  # clean up on failure
        messages.error(request, f'Could not process images: {exc}')
        return render(request, 'billing/new_bill.html')

    # 4. Atomic item persistence in central DB
    with transaction.atomic():
        total = Decimal('0')
        for item_data in result.get('items', []):
            qty = Decimal(str(item_data['quantity']))
            price = Decimal(str(item_data['unit_price']))
            item_total = qty * price
            total += item_total
            TransactionItem.objects.create(
                transaction=txn,
                product_name=item_data['product_name'],
                quantity=qty,
                unit_price=price,
                total_price=item_total,
                remark=item_data.get('remark', ''),
            )

        txn.remarks = result.get('remarks', '')
        txn.total_amount = total
        txn.save()

    messages.success(request, f'Bill #{txn.pk} analyzed! Review and edit items below.')
    return redirect('billing:review', pk=txn.pk)


@login_required
def review_view(request, pk):
    """
    Review & edit bill items before final confirmation.
    Any cashier or admin can access and collaborate on central bills.
    """
    txn = get_object_or_404(Transaction.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        if txn.status == Transaction.STATUS_CONFIRMED:
            messages.info(request, 'This bill has already been confirmed and locked.')
            return redirect('billing:history')

        names = request.POST.getlist('product_name')
        quantities = request.POST.getlist('quantity')
        unit_prices = request.POST.getlist('unit_price')

        if not any(n.strip() for n in names):
            messages.error(request, 'Bill cannot be empty.')
            return redirect('billing:review', pk=pk)

        with transaction.atomic():
            # Rebuild items atomically
            txn.items.all().delete()
            total = Decimal('0')

            for name, qty_str, price_str in zip(names, quantities, unit_prices):
                name = name.strip()
                if not name:
                    continue
                try:
                    qty = Decimal(qty_str)
                    price = Decimal(price_str)
                except Exception:
                    continue
                if qty <= 0 or price < 0:
                    continue
                item_total = qty * price
                total += item_total
                TransactionItem.objects.create(
                    transaction=txn,
                    product_name=name,
                    quantity=qty,
                    unit_price=price,
                    total_price=item_total,
                )

            txn.total_amount = total
            txn.notes = request.POST.get('notes', '').strip()
            txn.save()

        messages.success(request, f'Bill #{txn.pk} updated.')
        return redirect('billing:review', pk=pk)

    # Generate offline UPI QR code for the current total
    qr_code_b64, upi_uri = generate_upi_qr_base64(txn.total_amount, txn.pk)

    context = {
        'txn': txn,
        'qr_code_b64': qr_code_b64,
        'upi_uri': upi_uri,
        'store_upi_id': settings.STORE_UPI_ID,
        'store_name': settings.STORE_NAME,
    }
    return render(request, 'billing/review.html', context)


@login_required
def confirm_view(request, pk):
    """
    Locks and confirms the transaction in the store's central DB,
    recording the payment method (Cash, UPI, Card) and customer phone.
    """
    if request.method != 'POST':
        return redirect('billing:review', pk=pk)

    with transaction.atomic():
        txn = get_object_or_404(
            Transaction.objects.select_for_update(),
            pk=pk,
            status=Transaction.STATUS_REVIEW
        )

        if txn.items.count() == 0:
            messages.error(request, 'Cannot confirm an empty bill.')
            return redirect('billing:review', pk=pk)

        # Record payment details
        txn.payment_method = request.POST.get('payment_method', Transaction.PAYMENT_CASH)
        txn.customer_phone = request.POST.get('customer_phone', '').strip()
        txn.status = Transaction.STATUS_CONFIRMED
        txn.confirmed_at = timezone.now()
        txn.save()

    messages.success(request, f'✅ Bill #{txn.pk} confirmed! Paid via {txn.get_payment_method_display()}.')
    return redirect('billing:receipt', pk=txn.pk)


@login_required
def receipt_view(request, pk):
    """
    Clean printable view for a confirmed bill with Cashier details,
    one-click WhatsApp customer distribution, and thermal print formatting.
    """
    txn = get_object_or_404(Transaction.objects.select_related('user'), pk=pk)
    receipt_url = request.build_absolute_uri(reverse('billing:receipt', args=[txn.pk]))

    # Format customer WhatsApp receipt text
    cashier_name = txn.user.get_full_name() or txn.user.username
    date_str = txn.confirmed_at.strftime('%d %b %Y, %I:%M %p') if txn.confirmed_at else txn.created_at.strftime('%d %b %Y')

    lines = [
        f"🛒 *{settings.STORE_NAME}*",
        f"Bill #{txn.pk} &middot; {date_str}",
        f"Cashier: {cashier_name}",
        "--------------------------------",
    ]
    for item in txn.items.all():
        lines.append(f"• {item.product_name} x {item.quantity} = ₹{item.total_price}")
    lines.append("--------------------------------")
    lines.append(f"*TOTAL: ₹{txn.total_amount}* ({txn.get_payment_method_display()})")
    lines.append("")
    lines.append(f"Digital Receipt: {receipt_url}")
    lines.append("Thank you for shopping with us! 🙏")

    whatsapp_msg = "\n".join(lines)
    whatsapp_encoded = urllib.parse.quote(whatsapp_msg)

    # Customer WhatsApp direct link
    phone_digits = ''.join(c for c in txn.customer_phone if c.isdigit())
    if phone_digits:
        # Prepend 91 if 10-digit Indian mobile number
        if len(phone_digits) == 10:
            phone_digits = '91' + phone_digits
        customer_wa_link = f"https://api.whatsapp.com/send?phone={phone_digits}&text={whatsapp_encoded}"
    else:
        customer_wa_link = f"https://api.whatsapp.com/send?text={whatsapp_encoded}"

    context = {
        'txn': txn,
        'receipt_url': receipt_url,
        'whatsapp_msg': whatsapp_msg,
        'whatsapp_encoded': whatsapp_encoded,
        'customer_wa_link': customer_wa_link,
        'store_name': settings.STORE_NAME,
    }
    return render(request, 'billing/receipt.html', context)


@login_required
def delete_view(request, pk):
    """Delete / void a transaction (Admin or the cashier who created it)."""
    if request.method != 'POST':
        return redirect('billing:history')

    txn = get_object_or_404(Transaction, pk=pk)
    if not request.user.is_staff and txn.user != request.user:
        messages.error(request, 'Only the admin or the original cashier can delete this bill.')
        return redirect('billing:history')

    bill_id = txn.pk
    txn.delete()
    messages.success(request, f'Bill #{bill_id} deleted successfully.')
    return redirect('billing:history')
