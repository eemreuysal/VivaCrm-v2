from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from products.models import Product
from customers.models import Customer


class ExcelUploadHistoryAPIView(APIView):
    """API endpoint for Excel upload history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get recent Excel upload history"""
        try:
            # Mock data for now - later this can be connected to an actual upload tracking model
            # In a real implementation, you'd have an ExcelUpload model that tracks these uploads
            
            # Get recent data based on creation dates
            now = timezone.now()
            last_7_days = []
            
            for i in range(7):
                date = now - timedelta(days=i)
                
                # Count items created on this day
                order_count = Order.objects.filter(
                    created_at__date=date.date()
                ).count()
                
                product_count = Product.objects.filter(
                    created_at__date=date.date()
                ).count()
                
                customer_count = Customer.objects.filter(
                    created_at__date=date.date()
                ).count()
                
                if order_count > 0 or product_count > 0 or customer_count > 0:
                    # Türkçe tarih formatı
                    import locale
                    try:
                        locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
                    except:
                        pass
                    
                    if i == 0:
                        date_str = 'Bugün ' + date.strftime('%H:%M')
                    elif i == 1:
                        date_str = 'Dün ' + date.strftime('%H:%M')
                    else:
                        date_str = date.strftime('%d %B %H:%M')
                    
                    last_7_days.append({
                        'id': i + 1,
                        'date': date_str,
                        'orderCount': order_count,
                        'productCount': product_count,
                        'customerCount': customer_count
                    })
            
            # Return only the most recent 5 uploads
            return Response({
                'uploads': last_7_days[:5]
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)