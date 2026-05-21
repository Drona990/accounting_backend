from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication 
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsAdminOrSuperuser
from transaction.models import FinancialNoteHeader, NoteLedger
from transaction.serializers.financial_note_serializers import FinancialNoteHeaderSerializer

class FinancialNoteViewSet(viewsets.ModelViewSet):
    queryset = FinancialNoteHeader.objects.filter(delflag=' ').prefetch_related('details')
    serializer_class = FinancialNoteHeaderSerializer
    
    # 🔒 SECURE LOCK: JWT validation middleware maps with strict permissions check
    authentication_classes = [JWTAuthentication] 
    permission_classes = [IsAdminOrSuperuser]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['note_type', 'reason', 'customer', 'supplier']
    search_fields = ['note_no', 'original_invoice_no', 'name', 'gst_number']
    ordering_fields = ['created_at', 'note_date', 'grand_total']
    ordering = ['-created_at']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        note_instance = serializer.save()
        
        return Response(
            FinancialNoteHeaderSerializer(note_instance).data, 
            status=status.HTTP_201_CREATED
        )

    def perform_destroy(self, instance):
        instance.delflag = 'X'
        instance.save()
        NoteLedger.objects.filter(note_no=instance.note_no).update(delflag='X')