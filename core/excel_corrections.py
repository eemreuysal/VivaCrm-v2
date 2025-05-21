"""
Excel automatic correction system
"""
import re
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from django.db.models import Q
from products.models import Category


class AutoCorrector:
    """Otomatik düzeltme sınıfı"""
    
    def __init__(self):
        self.correction_history: List[Dict[str, Any]] = []
        self._categories_cache = None  # Cache for categories
        
    def correct_price(self, value: Any) -> Tuple[Optional[Decimal], bool]:
        """
        Fiyat formatını düzelt
        Returns: (düzeltilmiş_değer, düzeltildi_mi)
        """
        if value is None or str(value).strip() == "":
            return None, False
            
        value_str = str(value).strip()
        original_value = value_str
        
        # Özel karakterleri temizle
        value_str = re.sub(r'[^\d,.\-]', '', value_str)
        
        # Virgülü noktaya çevir
        if ',' in value_str and '.' not in value_str:
            value_str = value_str.replace(',', '.')
        elif ',' in value_str and '.' in value_str:
            # Eğer hem virgül hem nokta varsa, virgül binlik ayracı olabilir
            if value_str.index(',') < value_str.index('.'):
                value_str = value_str.replace(',', '')
            else:
                value_str = value_str.replace(',', '.')
                
        # Birden fazla nokta varsa temizle
        parts = value_str.split('.')
        if len(parts) > 2:
            value_str = '.'.join([parts[0], parts[-1]])
            
        try:
            corrected_value = Decimal(value_str)
            was_corrected = original_value != str(corrected_value)
            
            if was_corrected:
                self._log_correction('price', original_value, str(corrected_value))
                
            return corrected_value, was_corrected
        except (InvalidOperation, ValueError):
            return None, False
            
    def correct_date(self, value: Any) -> Tuple[Optional[datetime], bool]:
        """
        Tarih formatını düzelt
        Returns: (düzeltilmiş_değer, düzeltildi_mi)
        """
        if value is None or str(value).strip() == "":
            return None, False
            
        value_str = str(value).strip()
        original_value = value_str
        
        # Excel tarih numarasını kontrol et
        try:
            if isinstance(value, (int, float)):
                # Excel'in tarih sistemini dönüştür
                excel_date = int(value)
                if 1 <= excel_date <= 60000:  # Makul tarih aralığı
                    base_date = datetime(1900, 1, 1)
                    corrected_date = base_date + timedelta(days=excel_date - 2)
                    self._log_correction('date', original_value, corrected_date.strftime('%d/%m/%Y'))
                    return corrected_date, True
        except:
            pass
            
        # Farklı tarih formatlarını dene
        date_formats = [
            "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y",
            "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d",
            "%d/%m/%y", "%d.%m.%y", "%d-%m-%y",
            "%m/%d/%Y", "%m.%d.%Y", "%m-%d-%Y"
        ]
        
        for date_format in date_formats:
            try:
                corrected_date = datetime.strptime(value_str, date_format)
                was_corrected = original_value != corrected_date.strftime('%d/%m/%Y')
                
                if was_corrected:
                    self._log_correction('date', original_value, corrected_date.strftime('%d/%m/%Y'))
                    
                return corrected_date, was_corrected
            except ValueError:
                continue
                
        return None, False
        
    def correct_sku(self, value: Any) -> Tuple[Optional[str], bool]:
        """
        SKU formatını düzelt
        Returns: (düzeltilmiş_değer, düzeltildi_mi)
        """
        if value is None or str(value).strip() == "":
            return None, False
            
        value_str = str(value).strip()
        original_value = value_str
        
        # Büyük harfe çevir
        corrected_sku = value_str.upper()
        
        # Türkçe karakterleri değiştir
        tr_chars = {'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U',
                   'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u'}
        for tr_char, en_char in tr_chars.items():
            corrected_sku = corrected_sku.replace(tr_char, en_char)
            
        # Boşlukları alt çizgi ile değiştir
        corrected_sku = corrected_sku.replace(' ', '_')
        
        # Özel karakterleri temizle (harf, rakam, tire ve alt çizgi hariç)
        corrected_sku = re.sub(r'[^A-Z0-9\-_]', '', corrected_sku)
        
        # Birden fazla alt çizgi veya tireyi tekile indir
        corrected_sku = re.sub(r'[-_]{2,}', '_', corrected_sku)
        
        # Başında veya sonunda alt çizgi/tire varsa temizle
        corrected_sku = corrected_sku.strip('-_')
        
        was_corrected = original_value != corrected_sku
        
        if was_corrected:
            self._log_correction('sku', original_value, corrected_sku)
            
        return corrected_sku, was_corrected
        
    def correct_stock(self, value: Any) -> Tuple[Optional[int], bool]:
        """
        Stok değerini düzelt
        Returns: (düzeltilmiş_değer, düzeltildi_mi)
        """
        if value is None or str(value).strip() == "":
            return 0, True  # Boş stok değerlerini 0 olarak kabul et
            
        value_str = str(value).strip()
        original_value = value_str
        
        # Sayısal olmayan karakterleri temizle
        value_str = re.sub(r'[^\d\-]', '', value_str)
        
        try:
            corrected_stock = int(value_str)
            # Negatif stok değerlerini 0'a çevir
            if corrected_stock < 0:
                corrected_stock = 0
                
            was_corrected = original_value != str(corrected_stock)
            
            if was_corrected:
                self._log_correction('stock', original_value, str(corrected_stock))
                
            return corrected_stock, was_corrected
        except ValueError:
            return None, False
            
    def find_similar_category(self, value: str, threshold: float = 0.7) -> Tuple[Optional[str], float]:
        """
        Benzer kategori bul
        Returns: (kategori_adı, benzerlik_skoru)
        """
        if not value:
            return None, 0.0
            
        value_clean = value.strip().lower()
        
        # Cache categories to avoid N+1 queries
        if self._categories_cache is None:
            self._categories_cache = list(Category.objects.all().values('id', 'name', 'slug'))
        
        best_match = None
        best_score = 0.0
        
        for category in self._categories_cache:
            # Kategori adı ile karşılaştır
            name_score = SequenceMatcher(None, value_clean, category['name'].lower()).ratio()
            
            # Kategori slug ile karşılaştır
            slug_score = SequenceMatcher(None, value_clean, category['slug'].lower()).ratio()
            
            # En yüksek skoru al
            score = max(name_score, slug_score)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = category['name']
                
        return best_match, best_score
        
    def correct_category(self, value: Any, create_if_not_exists: bool = True) -> Tuple[Optional[str], bool]:
        """
        Kategori adını düzelt ve gerekirse yeni kategori oluştur
        Returns: (düzeltilmiş_değer, düzeltildi_mi)
        """
        if value is None or str(value).strip() == "":
            return None, False
            
        value_str = str(value).strip()
        original_value = value_str
        
        # Önce tam eşleşme kontrol et
        exact_match = Category.objects.filter(
            Q(name__iexact=value_str) | Q(slug__iexact=value_str)
        ).first()
        
        if exact_match:
            was_corrected = original_value != exact_match.name
            if was_corrected:
                self._log_correction('category', original_value, exact_match.name)
            return exact_match.name, was_corrected
            
        # Benzer kategori bul
        similar_category, score = self.find_similar_category(value_str)
        
        # Eğer benzerlik skoru yüksekse (0.85 ve üzeri) o kategoriyi kullan
        if similar_category and score >= 0.85:
            self._log_correction('category', original_value, similar_category, 
                               extra_data={'similarity_score': score})
            return similar_category, True
            
        # Düşük benzerlik skoru veya eşleşme yok, yeni kategori oluştur
        if create_if_not_exists:
            from django.utils.text import slugify
            new_category = Category.objects.create(
                name=value_str,
                slug=slugify(value_str),
                description=f"Excel import'tan otomatik oluşturuldu - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                is_active=True
            )
            self._log_correction('category', original_value, new_category.name, 
                               extra_data={'action': 'created_new', 'similarity_score': score})
            # Cache'i güncelle
            if self._categories_cache is not None:
                self._categories_cache = list(Category.objects.all().values('id', 'name', 'slug'))
            return new_category.name, True
            
        return None, False
        
    def _log_correction(self, field_type: str, original: Any, 
                       corrected: Any, extra_data: Optional[Dict] = None) -> None:
        """Düzeltme geçmişini kaydet"""
        log_entry = {
            'field_type': field_type,
            'original': original,
            'corrected': corrected,
            'timestamp': datetime.now().isoformat()
        }
        
        if extra_data:
            log_entry.update(extra_data)
            
        self.correction_history.append(log_entry)
        
    def get_correction_summary(self) -> Dict[str, Any]:
        """Düzeltme özeti"""
        summary = {
            'total_corrections': len(self.correction_history),
            'corrections_by_type': {},
            'recent_corrections': self.correction_history[-10:]
        }
        
        for correction in self.correction_history:
            field_type = correction['field_type']
            if field_type not in summary['corrections_by_type']:
                summary['corrections_by_type'][field_type] = 0
            summary['corrections_by_type'][field_type] += 1
            
        return summary
        
    def clear_history(self) -> None:
        """Düzeltme geçmişini temizle"""
        self.correction_history.clear()


class BulkCorrector:
    """Toplu düzeltme sınıfı"""
    
    def __init__(self):
        self.auto_corrector = AutoCorrector()
        
    def correct_data_frame(self, df, correction_rules: Dict[str, str]) -> Tuple[Any, Dict[str, Any]]:
        """
        DataFrame üzerinde toplu düzeltme yap
        
        Args:
            df: Pandas DataFrame
            correction_rules: {column_name: correction_type} mapping
            
        Returns:
            (düzeltilmiş_df, düzeltme_sonuçları)
        """
        import pandas as pd
        
        corrected_df = df.copy()
        results = {
            'total_corrections': 0,
            'corrections_by_column': {},
            'failed_corrections': []
        }
        
        for column, correction_type in correction_rules.items():
            if column not in corrected_df.columns:
                continue
                
            corrections_made = 0
            
            for idx, value in corrected_df[column].items():
                if pd.isna(value):
                    continue
                    
                corrected_value = None
                was_corrected = False
                
                if correction_type == 'price':
                    corrected_value, was_corrected = self.auto_corrector.correct_price(value)
                elif correction_type == 'date':
                    corrected_value, was_corrected = self.auto_corrector.correct_date(value)
                elif correction_type == 'sku':
                    corrected_value, was_corrected = self.auto_corrector.correct_sku(value)
                elif correction_type == 'stock':
                    corrected_value, was_corrected = self.auto_corrector.correct_stock(value)
                elif correction_type == 'category':
                    corrected_value, was_corrected = self.auto_corrector.correct_category(value, create_if_not_exists=True)
                    
                if was_corrected and corrected_value is not None:
                    corrected_df.at[idx, column] = corrected_value
                    corrections_made += 1
                elif was_corrected and corrected_value is None:
                    results['failed_corrections'].append({
                        'row': idx,
                        'column': column,
                        'value': value,
                        'correction_type': correction_type
                    })
                    
            results['corrections_by_column'][column] = corrections_made
            results['total_corrections'] += corrections_made
            
        return corrected_df, results
        
    def apply_custom_corrections(self, df, custom_corrections: List[Dict[str, Any]]) -> Any:
        """
        Özel düzeltmeleri uygula
        
        Args:
            df: Pandas DataFrame
            custom_corrections: Liste içinde düzeltme tanımları
                [{
                    'row': int,
                    'column': str,
                    'new_value': Any
                }]
                
        Returns:
            düzeltilmiş_df
        """
        corrected_df = df.copy()
        
        for correction in custom_corrections:
            row = correction.get('row')
            column = correction.get('column')
            new_value = correction.get('new_value')
            
            if row is not None and column and column in corrected_df.columns:
                corrected_df.at[row, column] = new_value
                
        return corrected_df