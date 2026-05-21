import logging
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend 
from ..models import ChallanHeader, ProformaHeader
from ..serializers.chalan_serializers import ChallanHeaderSerializer, ProformaHeaderSerializer
from core.permissions import IsAdminOrSuperuser, IsAccountActive 

logger = logging.getLogger(__name__)

class ChallanViewSet(viewsets.ModelViewSet):
    queryset = ChallanHeader.objects.filter(delflag=' ').prefetch_related('details')
    serializer_class = ChallanHeaderSerializer
    permission_classes = [IsAdminOrSuperuser, IsAccountActive]

    # ✅ FIX: Enable industrial filtering backends for search and dynamic tabs query mapping
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dc_type'] # 👈 Flutter ka ?dc_type=INWARD/OUTWARD ab yahan se catch hoga!
    search_fields = ['billno', 'name', 'gst_number', 'purchase_order_no']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        logger.info(f"🚀 Attempting to execute Delivery Challan Transaction. Payload: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"✅ Challan Document Generated Successfully: {serializer.data.get('billno')}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"💥 DATABASE SAVE ERROR (Challan-Engine): {str(e)}", exc_info=True)
                return Response(
                    {"error": "Database runtime error occurred while committing Challan Transaction.", "details": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.warning(f"❌ SERIALIZER VALIDATION FAILURE (Challan-Engine): {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProformaViewSet(viewsets.ModelViewSet):
    queryset = ProformaHeader.objects.filter(delflag=' ').prefetch_related('details').order_by('-created_at')
    serializer_class = ProformaHeaderSerializer
    permission_classes = [IsAdminOrSuperuser, IsAccountActive]

    # ✅ FIX: Enable search architecture for proforma list maps too
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['billno', 'name', 'gst_number']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        logger.info(f"🚀 Attempting to instantiate Proforma Invoice. Payload: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"✅ Proforma Invoice Created Successfully: {serializer.data.get('billno')}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"💥 DATABASE SAVE ERROR (Proforma-Engine): {str(e)}", exc_info=True)
                return Response(
                    {"error": "Database error occurred while processing Proforma draft.", "details": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.warning(f"❌ VALIDATION FAILURE (Proforma-Engine): {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)