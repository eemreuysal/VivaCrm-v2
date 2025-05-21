"""
Customers modülü için servis katmanı.
Business logic kod tekrarını önlemek için merkezi bir yer sağlar.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.cache import cache
from django.utils.text import slugify
import logging
import pandas as pd
from typing import Dict, Any, List, Optional, Union

from .models import Customer, Address, Contact

logger = logging.getLogger(__name__)


class CustomerService:
    """
    Müşteri işlemleri için servis.
    """
    
    @staticmethod
    def validate_email_unique(email, customer_id=None):
        """
        Email adresinin benzersiz olduğunu doğrular.
        
        Args:
            email (str): Kontrol edilecek email
            customer_id (int, optional): Güncellemede hariç tutulacak müşteri ID
            
        Returns:
            bool: Email benzersiz ise True
            
        Raises:
            ValidationError: Email başka bir müşteride varsa
        """
        if not email:
            return True
            
        query = Customer.objects.filter(email=email)
        if customer_id:
            query = query.exclude(id=customer_id)
            
        if query.exists():
            raise ValidationError(f"Bu email adresi başka bir müşteri tarafından kullanılıyor: {email}")
        
        return True
    
    @staticmethod
    def validate_phone_unique(phone, customer_id=None):
        """
        Telefon numarasının benzersiz olduğunu doğrular.
        
        Args:
            phone (str): Kontrol edilecek telefon
            customer_id (int, optional): Güncellemede hariç tutulacak müşteri ID
            
        Returns:
            bool: Telefon benzersiz ise True
            
        Raises:
            ValidationError: Telefon başka bir müşteride varsa
        """
        if not phone:
            return True
            
        query = Customer.objects.filter(phone=phone)
        if customer_id:
            query = query.exclude(id=customer_id)
            
        if query.exists():
            raise ValidationError(f"Bu telefon numarası başka bir müşteri tarafından kullanılıyor: {phone}")
        
        return True
    
    @staticmethod
    def normalize_phone_number(phone):
        """
        Telefon numarasını normalleştirir.
        
        Args:
            phone (str): Normalleştirilecek telefon numarası
            
        Returns:
            str: Normalleştirilmiş telefon numarası
        """
        if not phone:
            return ""
            
        # Sadece rakamları al
        digits = ''.join(c for c in phone if c.isdigit())
        
        # Türkiye için başında 0 varsa kaldır
        if digits.startswith('0'):
            digits = digits[1:]
            
        # Formatlama: XXX-XXX-XXXX
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        
        return phone
    
    @staticmethod
    def get_or_create_customer(name, email=None, phone=None, **kwargs):
        """
        Verilen bilgilere göre müşteri bulur veya oluşturur.
        
        Args:
            name (str): Müşteri adı
            email (str, optional): Email
            phone (str, optional): Telefon
            **kwargs: Diğer müşteri alanları
            
        Returns:
            tuple: (customer, created) - (Müşteri nesnesi, oluşturuldu mu?)
        """
        # Email veya telefon varsa, müşteriyi bul
        if email:
            customers = Customer.objects.filter(email=email)
            if customers.exists():
                return customers.first(), False
                
        if phone:
            normalized_phone = CustomerService.normalize_phone_number(phone)
            customers = Customer.objects.filter(phone=normalized_phone)
            if customers.exists():
                return customers.first(), False
        
        # Müşteri bulunamadı, yeni oluştur
        customer = Customer(
            name=name,
            email=email or "",
            phone=CustomerService.normalize_phone_number(phone) if phone else "",
            **kwargs
        )
        customer.save()
        
        # Önbelleği temizle
        cache.delete('customer_count')
        
        return customer, True
    
    @staticmethod
    def get_full_customer_data(customer_id):
        """
        Müşteri ve ilişkili tüm verileri getirir.
        
        Args:
            customer_id (int): Müşteri ID
            
        Returns:
            dict: Müşteri ve ilişkili tüm veriler
        """
        # Önbellekten kontrol et
        cache_key = f'customer_full_data_{customer_id}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
            
        try:
            # Müşteriyi ve ilişkili verileri getir
            customer = Customer.objects.select_related('owner').prefetch_related(
                'addresses', 'contacts', 'orders'
            ).get(id=customer_id)
            
            # Siparişleri getir
            orders = list(customer.orders.select_related('owner').order_by('-order_date')[:10])
            
            # Adresleri getir
            addresses = list(customer.addresses.all())
            
            # Kişileri getir
            contacts = list(customer.contacts.all())
            
            # Sonuçları hazırla
            data = {
                'customer': customer,
                'addresses': addresses,
                'contacts': contacts,
                'recent_orders': orders,
                'order_count': customer.total_orders,
                'total_revenue': customer.total_revenue
            }
            
            # Önbelleğe kaydet (1 saat)
            cache.set(cache_key, data, 3600)
            
            return data
            
        except Customer.DoesNotExist:
            logger.error(f"Müşteri bulunamadı: {customer_id}")
            return None
        except Exception as e:
            logger.error(f"Müşteri verileri getirilirken hata: {str(e)}")
            return None


class AddressService:
    """
    Adres işlemleri için servis.
    """
    
    @staticmethod
    @transaction.atomic
    def create_address(customer, title, address_type, address_line1, **kwargs):
        """
        Yeni adres oluşturur.
        
        Args:
            customer (Customer): Müşteri nesnesi
            title (str): Adres başlığı
            address_type (str): Adres tipi (billing, shipping, other)
            address_line1 (str): Adres satırı 1
            **kwargs: Diğer adres alanları
            
        Returns:
            Address: Oluşturulan adres
        """
        is_default = kwargs.pop('is_default', False)
        
        # Eğer varsayılan olarak işaretlendiyse, diğer varsayılanları kaldır
        if is_default:
            Address.objects.filter(customer=customer, is_default=True).update(is_default=False)
        
        # Adres oluştur
        address = Address.objects.create(
            customer=customer,
            title=title,
            type=address_type,
            address_line1=address_line1,
            is_default=is_default,
            **kwargs
        )
        
        # Hiç varsayılan adres yoksa ilk adresi varsayılan yap
        if not Address.objects.filter(customer=customer, is_default=True).exists():
            address.is_default = True
            address.save()
        
        # Önbelleği temizle
        cache.delete(f'customer_full_data_{customer.id}')
        
        return address
    
    @staticmethod
    @transaction.atomic
    def update_address(address_id, **kwargs):
        """
        Adres günceller.
        
        Args:
            address_id (int): Adres ID
            **kwargs: Güncellenecek alanlar
            
        Returns:
            Address: Güncellenen adres
        """
        try:
            address = Address.objects.select_related('customer').get(id=address_id)
            
            # Varsayılan ayarını kontrol et
            if kwargs.get('is_default', False) and not address.is_default:
                # Diğer varsayılanları kaldır
                Address.objects.filter(customer=address.customer, is_default=True).update(is_default=False)
            
            # Alanları güncelle
            for key, value in kwargs.items():
                if hasattr(address, key):
                    setattr(address, key, value)
            
            address.save()
            
            # Önbelleği temizle
            cache.delete(f'customer_full_data_{address.customer.id}')
            
            return address
            
        except Address.DoesNotExist:
            logger.error(f"Adres bulunamadı: {address_id}")
            raise ValueError(f"Adres bulunamadı: {address_id}")
    
    @staticmethod
    def delete_address(address_id):
        """
        Adres siler.
        
        Args:
            address_id (int): Adres ID
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            address = Address.objects.select_related('customer').get(id=address_id)
            customer_id = address.customer.id
            
            # Varsayılan mı kontrol et
            was_default = address.is_default
            
            # Adresi sil
            address.delete()
            
            # Eğer varsayılan adres silindiyse ve başka adresler varsa yeni varsayılan belirle
            if was_default:
                other_address = Address.objects.filter(customer_id=customer_id).first()
                if other_address:
                    other_address.is_default = True
                    other_address.save()
            
            # Önbelleği temizle
            cache.delete(f'customer_full_data_{customer_id}')
            
            return True
            
        except Address.DoesNotExist:
            logger.error(f"Adres bulunamadı: {address_id}")
            return False
        except Exception as e:
            logger.error(f"Adres silinirken hata: {str(e)}")
            return False


class ContactService:
    """
    İlgili kişi işlemleri için servis.
    """
    
    @staticmethod
    @transaction.atomic
    def create_contact(customer, name, **kwargs):
        """
        Yeni ilgili kişi oluşturur.
        
        Args:
            customer (Customer): Müşteri nesnesi
            name (str): Kişi adı
            **kwargs: Diğer kişi alanları
            
        Returns:
            Contact: Oluşturulan kişi
        """
        is_primary = kwargs.pop('is_primary', False)
        
        # Eğer birincil olarak işaretlendiyse, diğer birincilleri kaldır
        if is_primary:
            Contact.objects.filter(customer=customer, is_primary=True).update(is_primary=False)
        
        # Kişi oluştur
        contact = Contact.objects.create(
            customer=customer,
            name=name,
            is_primary=is_primary,
            **kwargs
        )
        
        # Hiç birincil kişi yoksa ilk kişiyi birincil yap
        if not Contact.objects.filter(customer=customer, is_primary=True).exists():
            contact.is_primary = True
            contact.save()
        
        # Önbelleği temizle
        cache.delete(f'customer_full_data_{customer.id}')
        
        return contact
    
    @staticmethod
    @transaction.atomic
    def update_contact(contact_id, **kwargs):
        """
        İlgili kişi günceller.
        
        Args:
            contact_id (int): Kişi ID
            **kwargs: Güncellenecek alanlar
            
        Returns:
            Contact: Güncellenen kişi
        """
        try:
            contact = Contact.objects.select_related('customer').get(id=contact_id)
            
            # Birincil ayarını kontrol et
            if kwargs.get('is_primary', False) and not contact.is_primary:
                # Diğer birincilleri kaldır
                Contact.objects.filter(customer=contact.customer, is_primary=True).update(is_primary=False)
            
            # Alanları güncelle
            for key, value in kwargs.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            
            contact.save()
            
            # Önbelleği temizle
            cache.delete(f'customer_full_data_{contact.customer.id}')
            
            return contact
            
        except Contact.DoesNotExist:
            logger.error(f"İlgili kişi bulunamadı: {contact_id}")
            raise ValueError(f"İlgili kişi bulunamadı: {contact_id}")
    
    @staticmethod
    def delete_contact(contact_id):
        """
        İlgili kişi siler.
        
        Args:
            contact_id (int): Kişi ID
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            contact = Contact.objects.select_related('customer').get(id=contact_id)
            customer_id = contact.customer.id
            
            # Birincil mi kontrol et
            was_primary = contact.is_primary
            
            # Kişiyi sil
            contact.delete()
            
            # Eğer birincil kişi silindiyse ve başka kişiler varsa yeni birincil belirle
            if was_primary:
                other_contact = Contact.objects.filter(customer_id=customer_id).first()
                if other_contact:
                    other_contact.is_primary = True
                    other_contact.save()
            
            # Önbelleği temizle
            cache.delete(f'customer_full_data_{customer_id}')
            
            return True
            
        except Contact.DoesNotExist:
            logger.error(f"İlgili kişi bulunamadı: {contact_id}")
            return False
        except Exception as e:
            logger.error(f"İlgili kişi silinirken hata: {str(e)}")
            return False


class CustomerImportService:
    """
    Müşteri içe aktarma işlemleri için servis.
    """
    
    @staticmethod
    def validate_customer_type(value):
        """
        Müşteri tipini doğrula.
        
        Args:
            value: Doğrulanacak değer
            
        Returns:
            str: Doğrulanmış müşteri tipi
            
        Raises:
            ValidationError: Geçersiz müşteri tipi
        """
        if not value:
            return 'individual'
        
        valid_types = ['individual', 'corporate']
        
        if isinstance(value, str) and value.lower() in valid_types:
            return value.lower()
        
        # Yaygın değerleri eşleştir
        if isinstance(value, str):
            if value.lower() in ['person', 'personal', 'private', 'bireysel']:
                return 'individual'
            if value.lower() in ['company', 'business', 'corp', 'kurumsal', 'şirket']:
                return 'corporate'
        
        raise ValidationError(f"Geçersiz müşteri tipi. Şunlardan biri olmalı: {', '.join(valid_types)}")
    
    @staticmethod
    def validate_address_type(value):
        """
        Adres tipini doğrula.
        
        Args:
            value: Doğrulanacak değer
            
        Returns:
            str: Doğrulanmış adres tipi
            
        Raises:
            ValidationError: Geçersiz adres tipi
        """
        if not value:
            return 'other'
        
        valid_types = ['billing', 'shipping', 'other']
        
        if isinstance(value, str) and value.lower() in valid_types:
            return value.lower()
        
        # Yaygın değerleri eşleştir
        if isinstance(value, str):
            if value.lower() in ['bill', 'invoice', 'fatura']:
                return 'billing'
            if value.lower() in ['ship', 'delivery', 'sevkiyat', 'teslimat']:
                return 'shipping'
        
        raise ValidationError(f"Geçersiz adres tipi. Şunlardan biri olmalı: {', '.join(valid_types)}")
    
    @staticmethod
    def validate_boolean(value):
        """
        Boolean değerleri doğrula ve ayrıştır.
        
        Args:
            value: Doğrulanacak değer
            
        Returns:
            bool: Doğrulanmış boolean değeri
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.lower()
            if value in ['true', 'yes', '1', 'y', 't', 'evet', 'e']:
                return True
            elif value in ['false', 'no', '0', 'n', 'f', 'hayır', 'h']:
                return False
        
        if isinstance(value, (int, float)):
            return bool(value)
        
        return False
    
    @staticmethod
    @transaction.atomic
    def import_customers_excel(file_obj, update_existing=True) -> Dict[str, Any]:
        """
        Excel dosyasından müşteri verilerini içe aktar.
        
        Args:
            file_obj: Excel dosyası
            update_existing: Mevcut müşterileri güncelle
            
        Returns:
            dict: İçe aktarma istatistikleri
        """
        try:
            # Excel dosyasını oku
            df = pd.read_excel(file_obj)
            df = df.fillna('')
            
            # Field mapping
            field_mapping = {
                'Customer Name *': 'name',
                'Customer Name': 'name',
                'Type (individual/corporate) *': 'type',
                'Type': 'type',
                'Company Name': 'company_name',
                'Tax Office': 'tax_office',
                'Tax/ID Number': 'tax_number',
                'Email *': 'email',
                'Email': 'email',
                'Phone *': 'phone',
                'Phone': 'phone',
                'Website': 'website',
                'Notes': 'notes'
            }
            
            # İçe aktarma istatistiklerini izle
            created_count = 0
            updated_count = 0
            error_count = 0
            error_rows = []
            
            # Her satırı işle
            for index, row in df.iterrows():
                try:
                    # Gerekli alanları kontrol et
                    name = row.get('Customer Name *') or row.get('Customer Name')
                    if not name:
                        raise ValidationError("Müşteri Adı zorunludur")
                    
                    # Müşteri tipi
                    customer_type = CustomerImportService.validate_customer_type(
                        row.get('Type (individual/corporate) *') or row.get('Type', '')
                    )
                    
                    # Email ve telefon
                    email = row.get('Email *') or row.get('Email', '')
                    phone = row.get('Phone *') or row.get('Phone', '')
                    
                    if not email and not phone:
                        raise ValidationError("Email veya Telefon zorunludur")
                    
                    # Diğer alanlar
                    company_name = row.get('Company Name', '')
                    tax_office = row.get('Tax Office', '')
                    tax_number = row.get('Tax/ID Number', '')
                    website = row.get('Website', '')
                    notes = row.get('Notes', '')
                    
                    # Telefonu normalleştir
                    normalized_phone = CustomerService.normalize_phone_number(phone)
                    
                    # Müşteri var mı kontrol et
                    customer = None
                    if update_existing:
                        if email:
                            try:
                                customer = Customer.objects.get(email=email)
                            except Customer.DoesNotExist:
                                pass
                        
                        if not customer and normalized_phone:
                            try:
                                customer = Customer.objects.get(phone=normalized_phone)
                            except Customer.DoesNotExist:
                                pass
                    
                    if customer:
                        # Müşteriyi güncelle
                        customer.name = name
                        customer.type = customer_type
                        customer.company_name = company_name
                        customer.tax_office = tax_office
                        customer.tax_number = tax_number
                        if email and not customer.email:
                            customer.email = email
                        if normalized_phone and not customer.phone:
                            customer.phone = normalized_phone
                        customer.website = website
                        customer.notes = notes
                        customer.save()
                        updated_count += 1
                    else:
                        # Yeni müşteri oluştur
                        Customer.objects.create(
                            name=name,
                            type=customer_type,
                            company_name=company_name,
                            tax_office=tax_office,
                            tax_number=tax_number,
                            email=email,
                            phone=normalized_phone,
                            website=website,
                            notes=notes,
                            is_active=True
                        )
                        created_count += 1
                    
                except Exception as e:
                    logger.error(f"Müşteri içe aktarma hatası (satır {index + 2}): {str(e)}")
                    error_count += 1
                    error_rows.append({
                        'row': index + 2,  # Excel satır numarası (1-tabanlı, artı başlık)
                        'data': row.to_dict(),
                        'error': str(e)
                    })
            
            # İstatistikleri döndür
            return {
                'created': created_count,
                'updated': updated_count,
                'error_count': error_count,
                'error_rows': error_rows,
                'total': len(df)
            }
            
        except Exception as e:
            logger.error(f"Excel dosyası işlenirken hata: {str(e)}")
            raise ValidationError(f"Excel dosyası işlenirken hata: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def import_addresses_excel(file_obj, update_existing=True) -> Dict[str, Any]:
        """
        Excel dosyasından adres verilerini içe aktar.
        
        Args:
            file_obj: Excel dosyası
            update_existing: Mevcut adresleri güncelle
            
        Returns:
            dict: İçe aktarma istatistikleri
        """
        try:
            # Excel dosyasını oku
            df = pd.read_excel(file_obj)
            df = df.fillna('')
            
            # İçe aktarma istatistiklerini izle
            created_count = 0
            updated_count = 0
            error_count = 0
            error_rows = []
            
            # Her satırı işle
            for index, row in df.iterrows():
                try:
                    # Müşteri emaili (zorunlu)
                    customer_email = row.get('Customer Email *') or row.get('Customer Email')
                    if not customer_email:
                        raise ValidationError("Müşteri Emaili zorunludur")
                    
                    # Müşteriyi bul
                    try:
                        customer = Customer.objects.get(email=customer_email)
                    except Customer.DoesNotExist:
                        raise ValidationError(f"{customer_email} emailli müşteri bulunamadı")
                    
                    # Adres verilerini al
                    title = row.get('Address Title *') or row.get('Address Title')
                    if not title:
                        raise ValidationError("Adres Başlığı zorunludur")
                    
                    address_type = CustomerImportService.validate_address_type(row.get('Address Type *') or row.get('Address Type', ''))
                    
                    address_line1 = row.get('Address Line 1 *') or row.get('Address Line 1')
                    if not address_line1:
                        raise ValidationError("Adres Satırı 1 zorunludur")
                    
                    city = row.get('City *') or row.get('City')
                    if not city:
                        raise ValidationError("Şehir zorunludur")
                    
                    # Opsiyonel alanlar
                    address_line2 = row.get('Address Line 2', '')
                    state = row.get('State/District', '')
                    postal_code = row.get('Postal Code', '')
                    country = row.get('Country', 'Türkiye')
                    is_default = CustomerImportService.validate_boolean(row.get('Default Address', False))
                    
                    # Adres mevcut mu kontrol et
                    address = None
                    if update_existing:
                        try:
                            address = Address.objects.get(
                                customer=customer,
                                title=title
                            )
                        except Address.DoesNotExist:
                            pass
                    
                    if address:
                        # Mevcut adresi güncelle
                        AddressService.update_address(address.id, 
                            type=address_type,
                            address_line1=address_line1,
                            address_line2=address_line2,
                            city=city,
                            state=state,
                            postal_code=postal_code,
                            country=country,
                            is_default=is_default
                        )
                        updated_count += 1
                    else:
                        # Yeni adres oluştur
                        AddressService.create_address(
                            customer=customer,
                            title=title,
                            address_type=address_type,
                            address_line1=address_line1,
                            address_line2=address_line2,
                            city=city,
                            state=state,
                            postal_code=postal_code,
                            country=country,
                            is_default=is_default
                        )
                        created_count += 1
                    
                except Exception as e:
                    logger.error(f"Adres içe aktarma hatası (satır {index + 2}): {str(e)}")
                    error_count += 1
                    error_rows.append({
                        'row': index + 2,
                        'data': row.to_dict(),
                        'error': str(e)
                    })
            
            # İstatistikleri döndür
            return {
                'created': created_count,
                'updated': updated_count,
                'error_count': error_count,
                'error_rows': error_rows,
                'total': len(df)
            }
            
        except Exception as e:
            logger.error(f"Adres dosyası işlenirken hata: {str(e)}")
            raise ValidationError(f"Adres dosyası işlenirken hata: {str(e)}")