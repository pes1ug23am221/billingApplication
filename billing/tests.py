from decimal import Decimal
from django.test import TestCase
from accounts.models import User
from billing.models import Transaction, TransactionItem
from billing.services.upi_service import generate_upi_qr_base64, get_upi_payload


class BillingTestCase(TestCase):
    def setUp(self):
        self.cashier1 = User.objects.create_user(
            username='cashier_alice',
            password='password123'
        )
        self.cashier2 = User.objects.create_user(
            username='cashier_bob',
            password='password123'
        )
        self.admin = User.objects.create_superuser(
            username='shop_admin',
            email='admin@store.com',
            password='password123'
        )
        self.client.login(username='cashier_alice', password='password123')

    def test_transaction_item_total_calculation(self):
        txn = Transaction.objects.create(user=self.cashier1)
        item = TransactionItem.objects.create(
            transaction=txn,
            product_name='Organic Apples',
            quantity=Decimal('2.5'),
            unit_price=Decimal('120.00'),
        )
        self.assertEqual(item.total_price, Decimal('300.00'))

    def test_confirm_transaction_flow(self):
        txn = Transaction.objects.create(user=self.cashier1, status=Transaction.STATUS_REVIEW)
        TransactionItem.objects.create(
            transaction=txn,
            product_name='Milk',
            quantity=Decimal('1'),
            unit_price=Decimal('50.00')
        )
        response = self.client.post(f'/billing/{txn.pk}/confirm/', {
            'payment_method': 'upi',
            'customer_phone': '9876543210',
        })
        # Redirects to receipt view
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'/billing/{txn.pk}/receipt/', response.url)

        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_CONFIRMED)
        self.assertEqual(txn.payment_method, 'upi')
        self.assertEqual(txn.customer_phone, '9876543210')
        self.assertIsNotNone(txn.confirmed_at)

    def test_single_store_synchronized_dashboard(self):
        # Cashier 1 bills ₹300
        Transaction.objects.create(
            user=self.cashier1,
            status=Transaction.STATUS_CONFIRMED,
            total_amount=Decimal('300.00')
        )
        # Cashier 2 bills ₹200
        Transaction.objects.create(
            user=self.cashier2,
            status=Transaction.STATUS_CONFIRMED,
            total_amount=Decimal('200.00')
        )
        # Pending bill from Cashier 2
        pending = Transaction.objects.create(
            user=self.cashier2,
            status=Transaction.STATUS_REVIEW,
            total_amount=Decimal('50.00')
        )

        # Cashier 1 views dashboard -> sees combined store sales of ₹500 and pending bill
        response = self.client.get('/billing/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['confirmed_count'], 2)
        self.assertEqual(response.context['total_sales'], Decimal('500.00'))
        self.assertEqual(response.context['pending_count'], 1)
        self.assertIn(pending, response.context['pending_bills'])

    def test_history_search_and_cashier_filtering(self):
        t1 = Transaction.objects.create(
            user=self.cashier1,
            status=Transaction.STATUS_CONFIRMED,
            total_amount=Decimal('500.00'),
            notes='Register 1 Morning'
        )
        t2 = Transaction.objects.create(
            user=self.cashier2,
            status=Transaction.STATUS_REVIEW,
            total_amount=Decimal('150.00'),
            notes='Counter 2'
        )

        # 1. Filter by cashier
        res = self.client.get('/billing/history/?cashier=cashier_bob')
        self.assertEqual(res.status_code, 200)
        self.assertIn(t2, res.context['transactions'])
        self.assertNotIn(t1, res.context['transactions'])

        # 2. Search query by note
        res = self.client.get('/billing/history/?q=Morning')
        self.assertEqual(res.status_code, 200)
        self.assertIn(t1, res.context['transactions'])
        self.assertNotIn(t2, res.context['transactions'])

    def test_upi_qr_service(self):
        payload = get_upi_payload(Decimal('350.50'), 42)
        self.assertIn('upi://pay?', payload)
        self.assertIn('am=350.50', payload)
        self.assertIn('tn=Bill+42', payload)

        qr_b64, uri = generate_upi_qr_base64(Decimal('350.50'), 42)
        self.assertTrue(qr_b64.startswith('data:image/png;base64,'))
        self.assertEqual(uri, payload)

    def test_receipt_view_whatsapp_and_distribution(self):
        txn = Transaction.objects.create(
            user=self.cashier1,
            status=Transaction.STATUS_CONFIRMED,
            total_amount=Decimal('150.00'),
            payment_method='upi',
            customer_phone='9876543210'
        )
        TransactionItem.objects.create(
            transaction=txn,
            product_name='Eggs',
            quantity=Decimal('1'),
            unit_price=Decimal('90.00')
        )

        res = self.client.get(f'/billing/{txn.pk}/receipt/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('whatsapp_msg', res.context)
        self.assertIn('customer_wa_link', res.context)
        # Should prefix 91 for Indian 10-digit mobile number
        self.assertIn('phone=919876543210', res.context['customer_wa_link'])

    def test_delete_permissions(self):
        txn = Transaction.objects.create(
            user=self.cashier1,
            status=Transaction.STATUS_CONFIRMED,
            total_amount=Decimal('100.00')
        )

        # Cashier 2 tries to delete Cashier 1's bill (should be denied)
        self.client.login(username='cashier_bob', password='password123')
        del_res = self.client.post(f'/billing/{txn.pk}/delete/')
        self.assertEqual(del_res.status_code, 302)
        self.assertTrue(Transaction.objects.filter(pk=txn.pk).exists())

        # Admin can delete it
        self.client.login(username='shop_admin', password='password123')
        admin_del_res = self.client.post(f'/billing/{txn.pk}/delete/')
        self.assertEqual(admin_del_res.status_code, 302)
        self.assertFalse(Transaction.objects.filter(pk=txn.pk).exists())
