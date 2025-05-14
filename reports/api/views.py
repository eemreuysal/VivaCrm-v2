from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from reports.models import SavedReport
from reports.services import ReportService
from .serializers import (
    SavedReportSerializer, SalesSummarySerializer, SalesByPeriodSerializer,
    TopProductSerializer, TopCategorySerializer, TopCustomerSerializer,
    InventoryReportSerializer, PaymentStatisticsSerializer,
    CustomerAcquisitionSerializer, SalesReportParamsSerializer,
    InventoryReportParamsSerializer, CustomerReportParamsSerializer
)


class IsOwnerOrSharedReport(permissions.BasePermission):
    """
    Custom permission to only allow owners of a report to edit it,
    and only allow viewing if the report is shared or the user is the owner.
    """
    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner
        if request.method not in permissions.SAFE_METHODS:
            return obj.owner == request.user
        
        # Read permissions are allowed to the owner or if the report is shared
        return obj.owner == request.user or obj.is_shared


class SavedReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing saved reports.
    """
    queryset = SavedReport.objects.all()
    serializer_class = SavedReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSharedReport]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'owner', 'is_shared']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter reports that are either owned by the user or shared.
        """
        user = self.request.user
        return SavedReport.objects.filter(
            Q(owner=user) | Q(is_shared=True)
        )
    
    def perform_create(self, serializer):
        """
        Set the owner to the current user.
        """
        serializer.save(owner=self.request.user)


class SalesReportView(APIView):
    """
    API endpoint for generating sales reports.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Validate parameters
        params_serializer = SalesReportParamsSerializer(data=request.data)
        params_serializer.is_valid(raise_exception=True)
        
        # Extract parameters
        params = params_serializer.validated_data
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        period = params.get('period', 'month')
        status = params.get('status')
        limit = params.get('limit', 10)
        
        # Generate sales summary
        sales_summary = ReportService.get_sales_summary(
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Generate sales by period
        sales_by_period = ReportService.get_sales_by_period(
            period=period,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Generate top products
        top_products = ReportService.get_top_products(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate top categories
        top_categories = ReportService.get_top_categories(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate payment statistics
        payment_stats = ReportService.get_payment_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        # Serialize the results
        summary_serializer = SalesSummarySerializer(sales_summary)
        period_serializer = SalesByPeriodSerializer(sales_by_period, many=True)
        products_serializer = TopProductSerializer(top_products, many=True)
        categories_serializer = TopCategorySerializer(top_categories, many=True)
        payment_serializer = PaymentStatisticsSerializer(payment_stats, many=True)
        
        # Return the combined results
        return Response({
            'summary': summary_serializer.data,
            'sales_by_period': period_serializer.data,
            'top_products': products_serializer.data,
            'top_categories': categories_serializer.data,
            'payment_statistics': payment_serializer.data,
            'parameters': params
        })
    
    def get(self, request):
        """
        Handle GET requests by using default parameters.
        """
        return self.post(request)


class InventoryReportView(APIView):
    """
    API endpoint for generating inventory reports.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Validate parameters
        params_serializer = InventoryReportParamsSerializer(data=request.data)
        params_serializer.is_valid(raise_exception=True)
        
        # Extract parameters
        params = params_serializer.validated_data
        category = params.get('category')
        low_stock_threshold = params.get('low_stock_threshold', 10)
        
        # Generate inventory report
        inventory_report = ReportService.get_inventory_status(
            category=category,
            low_stock_threshold=low_stock_threshold
        )
        
        # Serialize the results
        report_serializer = InventoryReportSerializer(inventory_report)
        
        # Return the results
        return Response({
            'inventory': report_serializer.data,
            'parameters': params
        })
    
    def get(self, request):
        """
        Handle GET requests by using default parameters.
        """
        return self.post(request)


class CustomerReportView(APIView):
    """
    API endpoint for generating customer reports.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Validate parameters
        params_serializer = CustomerReportParamsSerializer(data=request.data)
        params_serializer.is_valid(raise_exception=True)
        
        # Extract parameters
        params = params_serializer.validated_data
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        period = params.get('period', 'month')
        limit = params.get('limit', 10)
        
        # Generate top customers
        top_customers = ReportService.get_top_customers(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        # Generate customer acquisition
        customer_acquisition = ReportService.get_customer_acquisition(
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        # Serialize the results
        customers_serializer = TopCustomerSerializer(top_customers, many=True)
        acquisition_serializer = CustomerAcquisitionSerializer(customer_acquisition, many=True)
        
        # Return the combined results
        return Response({
            'top_customers': customers_serializer.data,
            'customer_acquisition': acquisition_serializer.data,
            'parameters': params
        })
    
    def get(self, request):
        """
        Handle GET requests by using default parameters.
        """
        return self.post(request)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def save_report(request):
    """
    API endpoint for saving a report configuration.
    """
    # Get report data
    name = request.data.get('name')
    report_type = request.data.get('type')
    description = request.data.get('description', '')
    parameters = request.data.get('parameters', {})
    is_shared = request.data.get('is_shared', False)
    
    # Validate required fields
    if not name or not report_type:
        return Response(
            {'error': 'Name and type are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create or update the report
    report_id = request.data.get('id')
    if report_id:
        # Update existing report
        try:
            report = SavedReport.objects.get(id=report_id)
            
            # Check if user has permission
            if report.owner != request.user:
                return Response(
                    {'error': 'You do not have permission to update this report'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            report.name = name
            report.type = report_type
            report.description = description
            report.parameters = parameters
            report.is_shared = is_shared
            report.save()
            
        except SavedReport.DoesNotExist:
            return Response(
                {'error': 'Report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Create new report
        report = SavedReport.objects.create(
            name=name,
            type=report_type,
            description=description,
            parameters=parameters,
            is_shared=is_shared,
            owner=request.user
        )
    
    # Return the saved report
    serializer = SavedReportSerializer(report)
    return Response(serializer.data)