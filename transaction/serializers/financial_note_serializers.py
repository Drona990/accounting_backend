from rest_framework import serializers
from django.db import transaction
from transaction.models import FinancialNoteDetail, FinancialNoteHeader, NoteLedger

class FinancialNoteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialNoteDetail
        fields = [
            'sno', 'product_name', 'uom', 'hsncode', 'qty', 'rate', 
            'amount', 'cgst_p', 'sgst_p', 'igst_p', 'cgst_amt', 'sgst_amt', 'igst_amt', 'total'
        ]

class FinancialNoteHeaderSerializer(serializers.ModelSerializer):
    details = FinancialNoteDetailSerializer(many=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    supplier_name = serializers.ReadOnlyField(source='supplier.name')

    class Meta:
        model = FinancialNoteHeader
        fields = [
            'note_no', 'note_type', 'note_date', 'customer', 'customer_name', 
            'supplier', 'supplier_name', 'original_invoice_no', 'original_invoice_date', 
            'reason', 'ewb_no', 'dispatch', 'name', 'address', 'city', 'pin', 'gst_number', 
            'total_pcs', 'total_taxable', 'cgst', 'sgst', 'igst', 'round_off', 
            'grand_total', 'amtin_words', 'narration', 'created_at', 'created_by', 'details'
        ]

    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('details')
        
        request = self.context.get('request')
        user_identity = "ADMIN"
        if request and request.user and request.user.is_authenticated:
            user_identity = request.user.username

        # 1. Parent Object Creation
        note_header = FinancialNoteHeader.objects.create(
            created_by=user_identity, 
            **validated_data
        )
        
        # 2. Sequential Calculation Loops Block
        calc_total_pcs = 0
        calc_total_taxable = 0
        calc_cgst_amt = 0
        calc_sgst_amt = 0
        calc_igst_amt = 0

        for item in details_data:
            qty = item.get('qty', 0)
            rate = item.get('rate', 0)
            cgst_p = item.get('cgst_p', 0)
            sgst_p = item.get('sgst_p', 0)
            igst_p = item.get('igst_p', 0)

            base_amount = qty * rate
            c_amt = (base_amount * cgst_p) / 100
            s_amt = (base_amount * sgst_p) / 100
            i_amt = (base_amount * igst_p) / 100
            row_total = base_amount + i_amt

            FinancialNoteDetail.objects.create(
                header=note_header,
                sno=item.get('sno'),
                product_name=item.get('product_name'),
                uom=item.get('uom'),
                hsncode=item.get('hsncode'),
                qty=qty,
                rate=rate,
                amount=base_amount,
                cgst_p=cgst_p,
                sgst_p=sgst_p,
                igst_p=igst_p,
                cgst_amt=c_amt,
                sgst_amt=s_amt,
                igst_amt=i_amt,
                total=row_total
            )

            calc_total_pcs += qty
            calc_total_taxable += base_amount
            calc_cgst_amt += c_amt
            calc_sgst_amt += s_amt
            calc_igst_amt += i_amt

        # 3. Round-off Matrix Allocation
        sub_total = calc_total_taxable + calc_igst_amt
        rounded_total = round(sub_total)
        calc_round_off = rounded_total - sub_total

        note_header.total_pcs = calc_total_pcs
        note_header.total_taxable = calc_total_taxable
        note_header.cgst = calc_cgst_amt
        note_header.sgst = calc_sgst_amt
        note_header.igst = calc_igst_amt
        note_header.round_off = calc_round_off
        note_header.grand_total = rounded_total
        note_header.save()

        # 4. LEDGER ROUTING INTERCEPTOR
        is_debit = note_header.note_type == 'DEBIT_NOTE'
        NoteLedger.objects.create(
            trdate=note_header.note_date,
            note_type=note_header.note_type,
            note_no=note_header.note_no,
            party_name=note_header.name,
            party_gst=note_header.gst_number,
            trdr=note_header.grand_total if is_debit else 0.00,
            trcr=0.00 if is_debit else note_header.grand_total,
            ctype="To" if is_debit else "By"
        )

        return note_header