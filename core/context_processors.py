"""
Core uygulaması için context processors.
"""

def default_notifications():
    """Varsayılan bildirimler."""
    return [
        {
            'type': 'info',
            'title': 'Yeni Sipariş!',
            'description': '5 dakika önce',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
        },
        {
            'type': 'warning',
            'title': 'Düşük Stok',
            'description': '3 ürünün stoğu azaldı',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />'
        },
        {
            'type': 'success',
            'title': 'Excel Import',
            'description': 'İşlem başarıyla tamamlandı',
            'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />'
        }
    ]

def sidebar_context(request):
    """
    Sidebar için varsayılan bölüm ve menü öğelerini sağlar.
    Bu, tüm şablonlarda kullanılabilir.
    """
    # Ana menü bölümü
    main_menu = {
        'title': 'Ana Menü',
        'items': [
            {
                'type': 'link',
                'title': 'Gösterge Paneli',
                'url': '/dashboard/',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />',
                'active': request.resolver_match.view_name == 'dashboard:dashboard',
            },
            {
                'type': 'link',
                'title': 'Müşteriler',
                'url': '/customers/',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />',
                'active': 'customer' in request.resolver_match.view_name if request.resolver_match else False,
            },
            {
                'type': 'link',
                'title': 'Ürünler',
                'url': '/products/',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />',
                'active': 'product' in request.resolver_match.view_name if request.resolver_match else False,
            },
            {
                'type': 'link',
                'title': 'Siparişler',
                'url': '/orders/',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />',
                'active': 'order' in request.resolver_match.view_name if request.resolver_match else False,
            },
        ]
    }
    
    # Excel işlemleri bölümü
    excel_menu = {
        'title': 'Excel İşlemleri',
        'items': [
            {
                'type': 'submenu',
                'title': 'Excel İşlemleri',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />',
                'open': 'excel' in request.resolver_match.view_name if request.resolver_match else False,
                'has_active': 'excel' in request.resolver_match.view_name if request.resolver_match else False,
                'items': [
                    {
                        'type': 'link',
                        'title': 'Ürün Yükle',
                        'url': '/products/import/',
                        'active': request.resolver_match.view_name == 'products:product-import' if request.resolver_match else False,
                    },
                    {
                        'type': 'link',
                        'title': 'Sipariş Yükle',
                        'url': '/orders/import/',
                        'active': request.resolver_match.view_name == 'orders:order-import' if request.resolver_match else False,
                    },
                    {
                        'type': 'link',
                        'title': 'Müşteri Yükle',
                        'url': '/customers/import/',
                        'active': request.resolver_match.view_name == 'customers:customer_import' if request.resolver_match else False,
                    },
                    {
                        'type': 'link',
                        'title': 'Stok Yükle',
                        'url': '/products/stock-adjustment/import/',
                        'active': request.resolver_match.view_name == 'products:stock-adjustment-import' if request.resolver_match else False,
                    },
                    {
                        'type': 'link',
                        'title': 'Ürün İndir',
                        'url': '/products/export/',
                        'active': request.resolver_match.view_name == 'products:export_products' if request.resolver_match else False,
                    },
                    {
                        'type': 'link',
                        'title': 'Sipariş İndir',
                        'url': '/orders/export/',
                        'active': request.resolver_match.view_name == 'orders:export_orders' if request.resolver_match else False,
                    },
                    {
                        'type': 'link',
                        'title': 'Müşteri İndir',
                        'url': '/customers/export/',
                        'active': request.resolver_match.view_name == 'customers:export_customers' if request.resolver_match else False,
                    },
                ]
            }
        ]
    }
    
    # Raporlar bölümü
    reports_menu = {
        'title': 'Raporlar',
        'items': [
            {
                'type': 'link',
                'title': 'Analiz Raporları',
                'url': '/reports/',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />',
                'active': 'report' in request.resolver_match.view_name if request.resolver_match else False,
            },
            {
                'type': 'link',
                'title': 'Faturalar',
                'url': '/invoices/',
                'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2L12 21l3.5-2 3.5 2z" />',
                'active': 'invoice' in request.resolver_match.view_name if request.resolver_match else False,
            },
        ]
    }
    
    # Yönetim bölümü (sadece staff üyeleri için)
    admin_menu = None
    if request.user.is_authenticated and request.user.is_staff:
        admin_menu = {
            'title': 'Yönetim',
            'items': [
                {
                    'type': 'link',
                    'title': 'Sistem Yönetimi',
                    'url': '/admin_panel/',
                    'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />',
                    'active': 'admin_panel' in request.resolver_match.app_name if request.resolver_match else False,
                },
                {
                    'type': 'link',
                    'title': 'Django Admin',
                    'url': '/admin/',
                    'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />',
                    'active': False,
                },
                {
                    'type': 'link',
                    'title': 'İmport Geçmişi',
                    'url': '/core/import-history/',
                    'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />',
                    'active': request.resolver_match.view_name == 'core:import-history' if request.resolver_match else False,
                },
                {
                    'type': 'link',
                    'title': 'Doğrulama Kuralları',
                    'url': '/core/validation/rules/',
                    'icon': '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />',
                    'active': request.resolver_match.view_name == 'core_validation:validation_rules_list' if request.resolver_match else False,
                },
            ]
        }
    
    # Tüm bölümleri bir araya getir
    sidebar_sections = [main_menu, excel_menu, reports_menu]
    if admin_menu:
        sidebar_sections.append(admin_menu)
    
    return {
        'default_sidebar_sections': sidebar_sections,
        'notifications': default_notifications(),
    }