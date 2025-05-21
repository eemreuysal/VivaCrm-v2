"""
Test views for the project.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.context_processors import default_notifications


@login_required
def test_dashboard(request):
    """Test view for the new modular dashboard."""
    
    # Örnek bildirimler oluştur
    test_notifications = default_notifications()
    
    # Test verisi oluştur
    context = {
        'page_title': 'Test Dashboard',
        'total_customers': 120,
        'total_orders': 45,
        'total_revenue': '₺5,250',
        'notifications': test_notifications,
        'notification_count': len(test_notifications),
    }
    return render(request, 'test_dashboard.html', context)