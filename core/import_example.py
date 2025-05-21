# core/import_example.py
"""
Excel içe aktarma sistemini kısmi başarı takibi ile kullanma örneği
"""
from core.excel import ExcelImporter
from core.models_import import ImportTask
from products.models import Product


def import_products_with_tracking(file_path, user):
    """Ürünleri içe aktarma - kısmi başarı takibi ile"""
    
    # İçe aktarma görevini oluştur
    import_task = ImportTask.objects.create(
        type='product',
        status='pending',
        file_name='products.xlsx',
        file_path=file_path,
        created_by=user
    )
    
    # Excel içe aktarıcıyı yapılandır
    importer = ExcelImporter(
        model=Product,
        field_mapping={
            'Ürün Kodu': 'code',
            'Ürün Adı': 'name',
            'Açıklama': 'description',
            'Fiyat': 'price',
            'Stok': 'stock',
            'Kategori': 'category_id',
            'Durum': 'is_active'
        },
        required_fields=['code', 'name', 'price'],
        unique_fields=['code'],
        validators={
            'price': lambda x: float(x) if x else 0,
            'stock': lambda x: int(x) if x else 0,
            'is_active': lambda x: x.lower() in ['true', '1', 'evet', 'aktif']
        }
    )
    
    try:
        # İçe aktarmayı başlat - ImportTask parametresini geç
        result = importer.import_data(
            file_obj=file_path,
            update_existing=True,
            import_task=import_task
        )
        
        # Sonuçları logla
        print(f"Toplam: {result.total}")
        print(f"Başarılı: {result.success} ({result.success_rate:.1f}%)")
        print(f"Kısmi Başarılı: {len(result.partial_success_rows)}")
        print(f"Başarısız: {result.failed}")
        print(f"Atlanan: {len(result.skipped_rows)}")
        
        # Detaylı rapor al
        if result.reporter:
            detailed_report = result.reporter.get_report()
            print("\nAlan Performansı:")
            for field_perf in detailed_report['field_performance']:
                print(f"- {field_perf['field']}: %{field_perf['success_rate']:.1f} başarılı")
        
        # Görevi tamamla
        import_task.status = 'completed' if result.failed == 0 else 'partial'
        import_task.save()
        
        return result
        
    except Exception as e:
        # Hata durumunda görevi güncelle
        import_task.status = 'failed'
        import_task.save()
        raise


# Kullanım örneği
if __name__ == "__main__":
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Test kullanıcısı
    user = User.objects.get(username='admin')
    
    # Excel dosyasını içe aktar
    result = import_products_with_tracking('products.xlsx', user)
    
    # Kısmi başarılı satırları kontrol et
    if result.partial_success_rows:
        print(f"\nKısmi başarılı satırlar: {result.partial_success_rows}")
        
        # Her kısmi başarılı satır için detayları göster
        for row_num in result.partial_success_rows:
            field_results = result.field_level_results.get(row_num, {})
            print(f"\nSatır {row_num}:")
            for field, success in field_results.items():
                status = "✓" if success else "✗"
                print(f"  {status} {field}")