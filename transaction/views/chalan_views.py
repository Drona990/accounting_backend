import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import ChallanHeader, ProformaHeader
from ..serializers.chalan_serializers import ChallanHeaderSerializer, ProformaHeaderSerializer
# Custom permission architecture imports
from core.permissions import IsAdminOrSuperuser, IsAccountActive 

logger = logging.getLogger(__name__)

class ChallanViewSet(viewsets.ModelViewSet):
    queryset = ChallanHeader.objects.filter(delflag=' ').order_by('-created_at')
    serializer_class = ChallanHeaderSerializer
    permission_classes = [IsAdminOrSuperuser, IsAccountActive]

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
    queryset = ProformaHeader.objects.filter(delflag=' ').order_by('-created_at')
    serializer_class = ProformaHeaderSerializer
    permission_classes = [IsAdminOrSuperuser, IsAccountActive]

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