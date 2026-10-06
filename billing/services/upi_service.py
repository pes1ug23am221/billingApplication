import io
import base64
import urllib.parse
import qrcode
from django.conf import settings


def get_upi_payload(total_amount, bill_id):
    """
    Generate standard NPCI UPI payment deep-link URI.
    Format: upi://pay?pa=<VPA>&pn=<PayeeName>&am=<Amount>&cu=INR&tn=Bill%20<ID>
    """
    vpa = settings.STORE_UPI_ID
    name = settings.STORE_NAME
    amount_str = f"{float(total_amount):.2f}"
    note = f"Bill {bill_id}"

    params = {
        'pa': vpa,
        'pn': name,
        'am': amount_str,
        'cu': 'INR',
        'tn': note,
    }
    query_string = urllib.parse.urlencode(params)
    return f"upi://pay?{query_string}"


def generate_upi_qr_base64(total_amount, bill_id):
    """
    Generates a high-contrast QR code as a base64 Data URI for inline HTML <img> tags.
    Works 100% offline without external internet or third-party APIs.
    """
    upi_uri = get_upi_payload(total_amount, bill_id)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64_str}", upi_uri
