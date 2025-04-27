import random
import string
from datetime import datetime


def generate_invoice_number():
    """Generate a unique invoice number with format: INV-YYYYMMDD-XXXXX"""
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"INV-{date_part}-{random_part}"
