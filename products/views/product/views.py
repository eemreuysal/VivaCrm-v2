"""
Product views for the products app.
"""
import logging
from datetime import datetime, timedelta

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Sum, Count
from django.utils.translation import gettext_lazy as _

from products.models import Product, Category, ProductAttribute, ProductAttributeValue
from products.forms.product import ProductForm, ProductSearchForm, ProductAdvancedSearchForm

logger = logging.getLogger(__name__)


class ProductListView(LoginRequiredMixin, FormMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    form_class = ProductSearchForm
    
    def get_template_names(self):
        return ['products/product_list.html']
        
    def get_form_kwargs(self):
        """Form için keyword argümanlarını alır."""
        kwargs = super().get_form_kwargs()
        # GET parametreleri varsa form'a aktar
        if self.request.method == 'GET':
            kwargs['data'] = self.request.GET.copy()
        return kwargs
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Get unique color values
        try:
            color_attr = ProductAttribute.objects.filter(name__icontains='renk').first()
            if color_attr:
                color_values = ProductAttributeValue.objects.filter(
                    attribute=color_attr
                ).values_list('value', flat=True).distinct().order_by('value')
                
                color_choices = [('', _('Tüm Renkler'))]
                color_choices.extend([(val, val) for val in color_values])
                form.fields['color'].choices = color_choices
        except:
            pass
            
        # Get unique size values
        try:
            size_attr = ProductAttribute.objects.filter(name__icontains='boyut').first()
            if size_attr:
                size_values = ProductAttributeValue.objects.filter(
                    attribute=size_attr
                ).values_list('value', flat=True).distinct().order_by('value')
                
                size_choices = [('', _('Tüm Boyutlar'))]
                size_choices.extend([(val, val) for val in size_values])
                form.fields['size'].choices = size_choices
        except:
            pass
            
        return form

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category', 'family').prefetch_related('images', 'attribute_values')
        
        # Debug loglama
        logger.info(f"REQUEST GET DATA: {self.request.GET}")
        
        # URL'den verileri doğrudan al
        query = self.request.GET.get('query', '').strip()
        category_id = self.request.GET.get('category', '').strip()
        family_id = self.request.GET.get('family', '').strip()
        color = self.request.GET.get('color', '').strip()
        size = self.request.GET.get('size', '').strip()
        price_min = self.request.GET.get('price_min', '').strip()
        price_max = self.request.GET.get('price_max', '').strip()
        sales_count = self.request.GET.get('sales_count', '').strip()
        status = self.request.GET.get('status', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        
        # Her filtre uygulamasının durumunu logla
        logger.info(f"Filtering with: query={query}, category={category_id}, family={family_id}, " 
                   f"color={color}, size={size}, price_min={price_min}, price_max={price_max}, "
                   f"sales_count={sales_count}, status={status}, date_from={date_from}, date_to={date_to}")
            
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(code__icontains=query) | 
                Q(sku__icontains=query) | 
                Q(barcode__icontains=query)
            )
            logger.info(f"After query filter: {queryset.count()} products")
        
        # Kategori filtreleme - ID'yi integer'a dönüştür
        if category_id:
            try:
                category_id_int = int(category_id)
                queryset = queryset.filter(category_id=category_id_int)
                logger.info(f"After category filter: {queryset.count()} products")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid category ID: {category_id}, error: {str(e)}")
            
        # Ürün ailesi filtreleme - ID'yi integer'a dönüştür
        if family_id:
            try:
                family_id_int = int(family_id)
                queryset = queryset.filter(family_id=family_id_int)
                logger.info(f"After family filter: {queryset.count()} products")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid family ID: {family_id}, error: {str(e)}")
            
        if color:
            # Renk özelliğine göre filtre
            queryset = queryset.filter(
                attribute_values__attribute__name__icontains='renk',
                attribute_values__value__icontains=color
            )
            logger.info(f"After color filter: {queryset.count()} products")
            
        if size:
            # Boyut özelliğine göre filtre
            queryset = queryset.filter(
                attribute_values__attribute__name__icontains='boyut',
                attribute_values__value__icontains=size
            )
            logger.info(f"After size filter: {queryset.count()} products")
                
        # Fiyat aralığı filtreleri
        if price_min:
            try:
                price_min_float = float(price_min)
                queryset = queryset.filter(price__gte=price_min_float)
                logger.info(f"After price_min filter: {queryset.count()} products")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid price_min: {price_min}, error: {str(e)}")
                
        if price_max:
            try:
                price_max_float = float(price_max)
                queryset = queryset.filter(price__lte=price_max_float)
                logger.info(f"After price_max filter: {queryset.count()} products")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid price_max: {price_max}, error: {str(e)}")
                
        # Satış adeti filtresi
        if sales_count:
            try:
                sales_count_int = int(sales_count)
                # Satış adeti filtresi için OrderItem tablosuna join yapılması gerekiyor
                try:
                    from orders.models import OrderItem, Order
                    from django.db.models import Count, Sum
                    
                    # Satış adeti >= sales_count olan ürün ID'lerini al
                    product_with_sales = OrderItem.objects.filter(
                        order__status__in=['completed', 'delivered']
                    ).values('product').annotate(
                        sales=Sum('quantity')
                    ).filter(sales__gte=sales_count_int).values_list('product', flat=True)
                    
                    queryset = queryset.filter(id__in=product_with_sales)
                    logger.info(f"After sales_count filter: {queryset.count()} products")
                except Exception as e:
                    # Orders app mevcut değilse veya hata varsa, filtre uygulamayı atla
                    logger.error(f"Error filtering by sales count: {str(e)}")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid sales_count: {sales_count}, error: {str(e)}")
                
        # Durum filtresi
        if status:
            queryset = queryset.filter(status=status)
            logger.info(f"After status filter: {queryset.count()} products")
                
        # Tarih aralığı filtresi - siparişlere göre ürünleri filtrele
        if date_from or date_to:
            try:
                from orders.models import OrderItem, Order
                from datetime import datetime, timedelta
                from django.utils import timezone
                
                # Tarih aralığındaki siparişleri içeren ürünleri bul
                order_query = Order.objects.all()
                
                if date_from:
                    try:
                        # String'i datetime'a çevir
                        if isinstance(date_from, str):
                            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                            date_from_datetime = datetime.combine(date_from_obj, datetime.min.time())
                            order_query = order_query.filter(order_date__gte=date_from_datetime)
                        else:
                            order_query = order_query.filter(order_date__gte=date_from)
                        logger.info(f"Date from filter applied: {date_from}")
                    except ValueError as e:
                        logger.error(f"Invalid date_from format: {date_from}, error: {str(e)}")
                
                if date_to:
                    try:
                        # String'i datetime'a çevir ve bir gün ekle (gün sonuna kadar)
                        if isinstance(date_to, str):
                            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                            next_day = date_to_obj + timedelta(days=1)
                            next_day_datetime = datetime.combine(next_day, datetime.min.time())
                            order_query = order_query.filter(order_date__lt=next_day_datetime)
                        else:
                            next_day = date_to + timedelta(days=1)
                            order_query = order_query.filter(order_date__lt=next_day)
                        logger.info(f"Date to filter applied: {date_to}, next_day: {next_day}")
                    except ValueError as e:
                        logger.error(f"Invalid date_to format: {date_to}, error: {str(e)}")
                
                # Belirtilen tarih aralığında sipariş verilen ürünleri al
                products_with_orders = OrderItem.objects.filter(
                    order__in=order_query
                ).values_list('product', flat=True).distinct()
                
                queryset = queryset.filter(id__in=products_with_orders)
                logger.info(f"After date range filter: {queryset.count()} products")
            except Exception as e:
                # Filtre uygulama hatası durumunda logla ve devam et
                logger.error(f"Error filtering products by date range: {str(e)}")
        
        # Sıralama için parametreleri al
        sort_by = self.request.GET.get('sort_by', 'name')
        sort_dir = self.request.GET.get('sort_dir', 'asc')
        
        # Sıralanabilir alanlar için eşleştirme
        field_mapping = {
            'code': 'code',
            'name': 'name',
            'category': 'category__name',
            'family': 'family__name',
            'price': 'price',
            'sales_count': 'total_sold',
            'sales_revenue': 'total_sales_revenue',
            'top_state': 'top_state'
        }
        
        # Sıralama alanını belirle
        sort_field = field_mapping.get(sort_by, 'name')
        if sort_dir == 'desc':
            sort_field = f'-{sort_field}'
        
        logger.info(f"Sorting by: {sort_field}")
        
        # Sıralama uygula
        result = queryset.order_by(sort_field)
        logger.info(f"Final result count after filtering and sorting: {result.count()} products")
        
        # Satış metriklerini ürünlere ekle
        try:
            from orders.models import OrderItem, Order
            from django.db.models import Count, Sum, F, Subquery, OuterRef
            
            # Her ürün için toplam satış adeti ve geliri hesapla
            sales_data = OrderItem.objects.filter(
                order__status__in=['completed', 'delivered']
            ).values('product').annotate(
                total_sold=Sum('quantity'),
                total_sales_revenue=Sum(F('unit_price') * F('quantity') - F('discount_amount'))
            )
            
            # Hızlı erişim için sözlük oluştur
            sales_lookup = {item['product']: item for item in sales_data}
            
            # Satış verilerini her ürüne ekle
            for product in result:
                sales_info = sales_lookup.get(product.id, {})
                product.total_sold = sales_info.get('total_sold', 0)
                product.total_sales_revenue = sales_info.get('total_sales_revenue', 0)
                
                # Eğer müşteri verisi varsa, en çok satış yapılan eyaleti bul
                try:
                    top_state_data = OrderItem.objects.filter(
                        product=product,
                        order__status__in=['completed', 'delivered']
                    ).values(
                        'order__customer__addresses__state'
                    ).annotate(
                        count=Count('id')
                    ).order_by('-count').first()
                    
                    if top_state_data and top_state_data['order__customer__addresses__state']:
                        product.top_state = top_state_data['order__customer__addresses__state']
                    else:
                        product.top_state = "Bilinmiyor"
                except Exception as e:
                    logger.error(f"Error getting top state for product {product.id}: {str(e)}")
                    product.top_state = "Bilinmiyor"
        except Exception as e:
            logger.error(f"Error attaching sales metrics to products: {str(e)}")
            # Eğer orders app mevcut değilse, varsayılan değerleri ayarla
            for product in result:
                product.total_sold = 0
                product.total_sales_revenue = 0
                product.top_state = "Bilinmiyor"
        
        return result
    
    def get_initial(self):
        """Form başlangıç değerlerini URL parametrelerinden al ve boş stringleri temizle"""
        logger.info(f"Getting initial form values from URL")
        
        initial = {
            'query': self.request.GET.get('query', '').strip(),
            'category': self.request.GET.get('category', '').strip(),
            'family': self.request.GET.get('family', '').strip(),
            'color': self.request.GET.get('color', '').strip(),
            'size': self.request.GET.get('size', '').strip(),
            'price_min': self.request.GET.get('price_min', '').strip(),
            'price_max': self.request.GET.get('price_max', '').strip(),
            'sales_count': self.request.GET.get('sales_count', '').strip(),
            'status': self.request.GET.get('status', '').strip(),
            'date_from': self.request.GET.get('date_from', '').strip(),
            'date_to': self.request.GET.get('date_to', '').strip(),
        }
        
        logger.info(f"Initial form values from URL: {initial}")
        
        # Boş değerleri none olarak ayarla
        for key, value in initial.items():
            if value == '':
                initial[key] = None
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Stok durumu bilgilerini context'e ekle
        context['low_stock_count'] = Product.objects.filter(
            is_physical=True, stock__gt=0, stock__lte=10
        ).count()
        context['out_of_stock_count'] = Product.objects.filter(
            is_physical=True, stock=0
        ).count()
        
        # Son 30 günde eklenen ürünler
        thirty_days_ago = datetime.now() - timedelta(days=30)
        context['new_products'] = Product.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Satış verilerini ekle
        try:
            from orders.models import OrderItem, Order
            from datetime import timedelta, datetime
            from django.utils import timezone
            from django.db.models import Sum
            
            # Tarih filtreleri uygulandıysa kullan
            order_query = Order.objects.filter(status__in=['completed', 'delivered'])
            date_from = self.request.GET.get('date_from', '').strip()
            date_to = self.request.GET.get('date_to', '').strip()
            
            # Tarih işleme ve format dönüşümü için detaylı loglama
            logger.info(f"Context data - processing date filters: from={date_from}, to={date_to}")
            
            if date_from:
                try:
                    # String'i datetime'a çevir
                    if isinstance(date_from, str):
                        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                        date_from_datetime = datetime.combine(date_from_obj, datetime.min.time())
                        order_query = order_query.filter(order_date__gte=date_from_datetime)
                    else:
                        order_query = order_query.filter(order_date__gte=date_from)
                    logger.info(f"Context data - date_from filter applied: {date_from}")
                except ValueError as e:
                    logger.error(f"Context data - invalid date_from format: {date_from}, error: {str(e)}")
                
            if date_to:
                try:
                    # String'i datetime'a çevir ve bir gün ekle (gün sonuna kadar)
                    if isinstance(date_to, str):
                        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                        next_day = date_to_obj + timedelta(days=1)
                        next_day_datetime = datetime.combine(next_day, datetime.min.time())
                        order_query = order_query.filter(order_date__lt=next_day_datetime)
                    else:
                        next_day = date_to + timedelta(days=1)
                        order_query = order_query.filter(order_date__lt=next_day)
                    logger.info(f"Context data - date_to filter applied: {date_to}, next_day: {next_day}")
                except ValueError as e:
                    logger.error(f"Context data - invalid date_to format: {date_to}, error: {str(e)}")
            
            # Tarih filtresi içindeki toplam satılan ürünleri hesapla
            total_sales = OrderItem.objects.filter(
                order__in=order_query
            ).aggregate(total=Sum('quantity'))
            context['total_sales_count'] = total_sales['total'] or 0
            
            # Tarih filtresi içindeki toplam satış gelirini hesapla
            total_revenue = OrderItem.objects.filter(
                order__in=order_query
            ).aggregate(total=Sum(F('unit_price') * F('quantity') - F('discount_amount')))
            context['total_sales_revenue'] = total_revenue['total'] or 0
            
            logger.info(f"Context data - calculated total sales: {context['total_sales_count']}, total revenue: {context['total_sales_revenue']}")
            
            # Gösterim için tarih filtrelerini context'e ekle
            context['date_from'] = date_from
            context['date_to'] = date_to
            
        except Exception as e:
            logger.error(f"Context data - error calculating sales data: {str(e)}")
            context['total_sales_count'] = 0
            context['total_sales_revenue'] = 0
        
        # Sıralama bilgilerini context'e ekle
        context['sort_by'] = self.request.GET.get('sort_by', 'name')
        context['sort_dir'] = self.request.GET.get('sort_dir', 'asc')
        
        # Tüm sütunlar için sıralama URL'lerini oluştur
        current_params = self.request.GET.copy()
        sort_urls = {}
        
        # Sıralanabilir alanları tanımla
        sortable_fields = ['code', 'name', 'category', 'family', 'price', 'sales_count', 'sales_revenue', 'top_state']
        
        for field in sortable_fields:
            params = current_params.copy()
            params['sort_by'] = field
            
            # Halihazırda bu alana göre sıralanıyorsa yönü değiştir
            current_sort = self.request.GET.get('sort_by')
            current_dir = self.request.GET.get('sort_dir')
            
            if current_sort == field and current_dir == 'asc':
                params['sort_dir'] = 'desc'
            else:
                params['sort_dir'] = 'asc'
                
            sort_urls[field] = f"?{params.urlencode()}"
        
        context['sort_urls'] = sort_urls
        logger.info(f"Context data - added sort information: {context['sort_by']} {context['sort_dir']}")
            
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        from products.forms.image import ProductImageForm
        from products.forms.attribute import ProductAttributeValueForm
        from products.forms.stock import StockMovementForm
        
        context = super().get_context_data(**kwargs)
        context['image_form'] = ProductImageForm()
        context['attribute_value_form'] = ProductAttributeValueForm(product=self.object)
        
        # Add stock movement information
        context['stock_movements'] = self.object.stock_movements.all()[:10]
        context['stock_movement_form'] = StockMovementForm(initial={'product': self.object})
        
        # Add sales history (if there are any OrderItems)
        try:
            from orders.models import OrderItem
            context['sales_history'] = OrderItem.objects.filter(
                product=self.object, 
                order__status__in=['completed', 'delivered']
            ).order_by('-order__order_date')[:10]
        except:
            pass
            
        return context


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_message = _("Ürün başarıyla oluşturuldu.")


class ProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_message = _("Ürün başarıyla güncellendi.")


class ProductDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:product-list')
    success_message = _("Ürün başarıyla silindi.")