from rest_framework import serializers
from django.db import transaction
from ..models import ChallanHeader, ChallanDetail, ProformaHeader, ProformaDetail, ChallanLedger

# --- CHALLAN SERIALIZERS ---
class ChallanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallanDetail
        exclude = ['header']

class ChallanHeaderSerializer(serializers.ModelSerializer):
    details = ChallanDetailSerializer(many=True)

    class Meta:
        model = ChallanHeader
        fields = '__all__'
        read_only_fields = ['billno']

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        dc_type = validated_data.get('dc_type')
        
        try:
            with transaction.atomic():
                # 1. Save Challan Header
                header = ChallanHeader.objects.create(**validated_data)
                
                # 2. Save Item Details
                for detail in details_data:
                    ChallanDetail.objects.create(header=header, **detail)

                # 3. Save to Challan Ledger (Dynamic Routing based on type)
                ctype_val = "To" if dc_type == "OUTWARD" else "By"
                
                ChallanLedger.objects.create(
                    dc_type=dc_type,
                    dc_no=header.billno,
                    dc_date=header.billdate,
                    party_name=header.name,
                    party_gst=header.gst_number,
                    ewb_no=header.ewb_no,
                    dispatch=header.dispatch,
                    estimated_value=header.grand_totamt,
                    ctype=ctype_val
                )
                return header
        except Exception as e:
            raise serializers.ValidationError({"error": f"Challan Transaction Error: {str(e)}"})


# --- PROFORMA SERIALIZERS ---
class ProformaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaDetail
        exclude = ['header']

class ProformaHeaderSerializer(serializers.ModelSerializer):
    details = ProformaDetailSerializer(many=True)

    class Meta:
        model = ProformaHeader
        fields = '__all__'
        read_only_fields = ['billno']

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        try:
            with transaction.atomic():
                # Proforma standard pipeline (Note: PI ka direct Ledger effect nahi hota jab tak conversion na ho)
                header = ProformaHeader.objects.create(**validated_data)
                
                for detail in details_data:
                    ProformaDetail.objects.create(header=header, **detail)
                    
                return header
        except Exception as e:
            raise serializers.ValidationError({"error": f"Proforma Transaction Error: {str(e)}"})