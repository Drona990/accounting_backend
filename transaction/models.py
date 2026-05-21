import string
import random
from django.db import models
from django.utils import timezone
from master.models import CustomerMaster, Ledger, SupplierMaster


# --- BILL/DC NUMBER GENERATORS ---
def generate_bill_no():
    prefix = "INV"
    year = timezone.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"

def generate_dc_no():
    prefix = "DC"
    year = timezone.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"

def generate_pi_no():
    prefix = "PI"
    year = timezone.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"


# --- ABSTRACT TRANSACTIONS MODIFIED ---

class BaseTransactionHeader(models.Model):
    billno = models.CharField(max_length=50, unique=True, default=generate_bill_no, editable=False)
    billdate = models.DateField()
    purchase_order_no = models.CharField(max_length=100, blank=True, null=True)
    purchase_order_date = models.DateField(blank=True, null=True)
    dc_no = models.CharField(max_length=100, blank=True, null=True)
    dc_date = models.DateField(blank=True, null=True)
    ewb_no = models.CharField(max_length=50, blank=True, null=True)
    dispatch = models.CharField(max_length=100, blank=True, null=True)

    no_of_package = models.CharField(max_length=50, blank=True, null=True)
    due_date = models.IntegerField(default=0)  # Due Days

    # Billing Info
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)

    # Financial Totals
    total_pcs = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    totalamount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Taxable
    forwading_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    igst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_totamt = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    amtin_words = models.TextField(blank=True, null=True)

    accno = models.CharField(max_length=100, blank=True, null=True)
    delflag = models.CharField(max_length=1, default=' ')
    deldate = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class BaseTransactionDetail(models.Model):
    sno = models.IntegerField()
    product_name = models.CharField(max_length=255)
    uom = models.CharField(max_length=50)
    hsncode = models.CharField(max_length=50, blank=True, null=True)
    qty = models.DecimalField(max_digits=15, decimal_places=2)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Base Amount
    cgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    igst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=15, decimal_places=2)  # Row Total with Tax
    remarks = models.TextField(blank=True, null=True)  # ✅ Jod diya Remarks UI compatibility ke liye

    class Meta:
        abstract = True


# ==========================================================================
# NEW FINAL TABLES FOR DELIVERY CHALLAN & PROFORMA INVOICE
# ==========================================================================

# --- 1. DELIVERY CHALLAN TABLES ---
class ChallanHeader(BaseTransactionHeader):
    DC_TYPE_CHOICES = (
        ('INWARD', 'Inward'),
        ('OUTWARD', 'Outward'),
    )
    dc_type = models.CharField(max_length=10, choices=DC_TYPE_CHOICES)
    billno = models.CharField(max_length=50, unique=True, default=generate_dc_no, editable=False)
    
    # Dono null/blank rakhe hain kyunki Inward me Supplier aayega, Outward me Customer
    customer = models.ForeignKey(CustomerMaster, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(SupplierMaster, on_delete=models.SET_NULL, null=True, blank=True)

class ChallanDetail(BaseTransactionDetail):
    header = models.ForeignKey(ChallanHeader, related_name='details', on_delete=models.CASCADE)


# --- 2. PROFORMA INVOICE TABLES ---
class ProformaHeader(BaseTransactionHeader):
    billno = models.CharField(max_length=50, unique=True, default=generate_pi_no, editable=False)
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE)

class ProformaDetail(BaseTransactionDetail):
    header = models.ForeignKey(ProformaHeader, related_name='details', on_delete=models.CASCADE)


# --- 3. CHALLAN LEDGER TABLE ---
class ChallanLedger(models.Model):
    tranno = models.AutoField(primary_key=True)
    trdate = models.DateField(default=timezone.now)
    dc_type = models.CharField(max_length=20)  # INWARD / OUTWARD
    dc_no = models.CharField(max_length=50)
    dc_date = models.DateField()
    party_name = models.CharField(max_length=255)
    party_gst = models.CharField(max_length=20, blank=True, null=True)
    ewb_no = models.CharField(max_length=50, blank=True, null=True)
    dispatch = models.CharField(max_length=100, blank=True, null=True)

    
    # Financial representation for stock value movement (Non-commercial values)
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ctype = models.CharField(max_length=10)  # To / By
    delflag = models.CharField(max_length=1, default=' ')

    class Meta:
        verbose_name = "Challan Ledger"
        verbose_name_plural = "Challan Ledgers"

# --- FINAL TABLES ---

class SalesHeader(BaseTransactionHeader):
    customer = models.ForeignKey(CustomerMaster, on_delete=models.CASCADE)

class SalesDetail(BaseTransactionDetail):
    header = models.ForeignKey(SalesHeader, related_name='details', on_delete=models.CASCADE)

class PurchaseHeader(BaseTransactionHeader):
    supplier = models.ForeignKey(SupplierMaster, on_delete=models.CASCADE)

class PurchaseDetail(BaseTransactionDetail):
    header = models.ForeignKey(PurchaseHeader, related_name='details', on_delete=models.CASCADE)



#---------------------------------***----------------------------------------------------

class BaseLedger(models.Model):
    # Image ke exact fields
    tranno = models.AutoField(primary_key=True)               # TRANNO (Auto Increment)
    trdate = models.DateField(default=timezone.now)           # TRDATE (Today's Date)
    invtype = models.CharField(max_length=20)
    invno = models.CharField(max_length=50) 
    invdate = models.DateField()                          # INVDATE (Bill Date)
    inname = models.CharField(max_length=255)                 # INNAME (Party Name)
    inaddress = models.TextField(blank=True, null=True)       # INADDRESS (Party Address)
    invgst = models.CharField(max_length=20, blank=True, null=True) # INVGST (Party GST)

    ewb_no = models.CharField(max_length=50, blank=True, null=True)
    dispatch = models.CharField(max_length=255, blank=True, null=True)
    
    # Accounting (Debit/Credit)
    trcr = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) # TRCR
    trdr = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) # TRDR
    ctype = models.CharField(max_length=10)                   # CTYPE (To / By)
    
    # Flags
    delflag = models.CharField(max_length=1, default=' ')     # DELFLAG
    deldate = models.DateField(null=True, blank=True)         # DELDATE

    class Meta:
        abstract = True

# --- FINAL SEPARATE TABLES ---

class SalesLedger(BaseLedger):
    class Meta:
        verbose_name = "Sales Ledger"
        verbose_name_plural = "Sales Ledgers"

class PurchaseLedger(BaseLedger):
    class Meta:
        verbose_name = "Purchase Ledger"
        verbose_name_plural = "Purchase Ledgers"



#---------------------------------***----------------------------------------------------


class CashTransaction(models.Model):
    VOUCHER_TYPES = (
        ('RECEIPT', 'Receipt'),
        ('PAYMENT', 'Payment'),
    )

    # Auto-incrementing Voucher Number
    voucher_no = models.AutoField(primary_key=True)
    
    # Sahi tarika date default set karne ka
    date = models.DateField(default=timezone.now) 
    
    # Ledger ke sath connection
    ledger = models.ForeignKey(
        'master.Ledger', 
        on_delete=models.PROTECT, 
        related_name='transactions'
    )
    
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    voucher_type = models.CharField(max_length=10, choices=VOUCHER_TYPES)
    narration = models.TextField(blank=True, null=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    # Isse pata chalega kisne entry ki
    created_by = models.CharField(max_length=100, default='ADMIN', editable=False)

    class Meta:
        ordering = ['-date', '-voucher_no']
        verbose_name = "Cash Transaction"
        verbose_name_plural = "Cash Transactions"

    def __str__(self):
        return f"{self.voucher_type} #{self.voucher_no} - {self.ledger.name}"
    
#-----------------------------------*****------------------------------------------------------
#-----------------------------------*****------------------------------------------------------


class JournalVoucher(models.Model):
    voucher_no = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateField()
    narration = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50, default='ADMIN')

    def save(self, *args, **kwargs):
        if not self.voucher_no:
            # Auto-generate Voucher Number (JV-0001, JV-0002...)
            last_v = JournalVoucher.objects.all().order_by('id').last()
            if not last_v:
                self.voucher_no = 'JV-0001'
            else:
                v_int = int(last_v.voucher_no.split('-')[1])
                self.voucher_no = f'JV-{str(v_int + 1).zfill(4)}'
        super(JournalVoucher, self).save(*args, **kwargs)

    def __str__(self):
        return self.voucher_no

class JournalItem(models.Model):
    TYPE_CHOICES = [('DEBIT', 'DEBIT'), ('CREDIT', 'CREDIT')]

    voucher = models.ForeignKey(JournalVoucher, related_name='items', on_delete=models.CASCADE)
    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.ledger.name} - {self.type} - {self.amount}"
    

#--------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------


# --- NOTE NUMBER GENERATORS ---
def generate_dn_no():
    prefix = "DN"
    year = timezone.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"

def generate_cn_no():
    prefix = "CN"
    year = timezone.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"


# --- CREDIT & DEBIT NOTE HEADERS ---
class FinancialNoteHeader(models.Model):
    NOTE_TYPE_CHOICES = (
        ('DEBIT_NOTE', 'Debit Note (Purchase Return)'),
        ('CREDIT_NOTE', 'Credit Note (Sales Return)'),
    )
    
    NOTE_REASONS = (
        ('DAMAGED_GOODS', 'Damaged Goods'),
        ('RATE_DIFFERENCE', 'Rate Difference'),
        ('SALES_RETURN', 'Sales Return'),
        ('PURCHASE_RETURN', 'Purchase Return'),
        ('SHORTAGE', 'Shortage / Less Quantity'),
    )

    note_no = models.CharField(max_length=50, unique=True, editable=False)
    note_type = models.CharField(max_length=15, choices=NOTE_TYPE_CHOICES)
    note_date = models.DateField(default=timezone.now)
    
    customer = models.ForeignKey(CustomerMaster, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(SupplierMaster, on_delete=models.SET_NULL, null=True, blank=True)
    
    original_invoice_no = models.CharField(max_length=100, blank=True, null=True, help_text="Original Bill Ref")
    original_invoice_date = models.DateField(blank=True, null=True)
    reason = models.CharField(max_length=30, choices=NOTE_REASONS)
    
    ewb_no = models.CharField(max_length=50, blank=True, null=True)
    dispatch = models.CharField(max_length=100, blank=True, null=True)
    
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)

    total_pcs = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_taxable = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    cgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    igst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    round_off = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    amtin_words = models.TextField(blank=True, null=True)

    narration = models.TextField(blank=True, null=True)
    delflag = models.CharField(max_length=1, default=' ')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, default='ADMIN')

    def save(self, *args, **kwargs):
        if not self.note_no:
            if self.note_type == 'DEBIT_NOTE':
                self.note_no = generate_dn_no()
            else:
                self.note_no = generate_cn_no()
        super().save(*args, **kwargs)


class FinancialNoteDetail(models.Model):
    header = models.ForeignKey(FinancialNoteHeader, related_name='details', on_delete=models.CASCADE)
    sno = models.IntegerField()
    product_name = models.CharField(max_length=255)
    uom = models.CharField(max_length=50)
    hsncode = models.CharField(max_length=50, blank=True, null=True)
    qty = models.DecimalField(max_digits=15, decimal_places=2)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=15, decimal_places=2)  
    cgst_p = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    sgst_p = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    igst_p = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    cgst_amt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sgst_amt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    igst_amt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=15, decimal_places=2)  

class NoteLedger(models.Model):
    tranno = models.AutoField(primary_key=True)
    trdate = models.DateField(default=timezone.now)
    note_type = models.CharField(max_length=20)  
    note_no = models.CharField(max_length=50)
    party_name = models.CharField(max_length=255)
    party_gst = models.CharField(max_length=20, blank=True, null=True)
    trcr = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    trdr = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ctype = models.CharField(max_length=10)      
    delflag = models.CharField(max_length=1, default=' ')