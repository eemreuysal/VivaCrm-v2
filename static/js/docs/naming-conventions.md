# VivaCRM JavaScript Naming Conventions

## Dosya İsimlendirme

### Kurallar
- Tüm dosya isimleri `kebab-case` (tire ile ayrılmış) olmalıdır
- Örnek: `user-profile.js`, `order-detail.js`, `api-helper.js`

### Dizin Yapısı
```
static/js/
├── core/               # Çekirdek modüller
│   ├── api.js         # API yardımcı fonksiyonları
│   ├── utils.js       # Utility fonksiyonları
│   ├── security.js    # Güvenlik yardımcıları
│   └── config.js      # Uygulama konfigürasyonu
├── components/         # Alpine.js componentleri
│   ├── dashboard.js
│   ├── orders.js
│   └── forms.js
├── modules/           # Özel modüller
│   └── charts.js
└── store/             # Global state management
    └── index.js
```

## Kod İsimlendirme

### Classes
- `PascalCase` kullanın
- Örnek: `ChartManager`, `ApiClient`, `UserProfile`

### Functions ve Methods
- `camelCase` kullanın
- Örnek: `getUserData()`, `formatCurrency()`, `handleSubmit()`

### Constants
- `UPPER_SNAKE_CASE` kullanın
- Örnek: `MAX_FILE_SIZE`, `API_TIMEOUT`, `DEFAULT_LOCALE`

### Variables
- `camelCase` kullanın
- Örnek: `userName`, `orderTotal`, `isLoading`

### Private Properties/Methods
- `_` prefix ile başlayın
- Örnek: `_privateMethod()`, `_internalState`

## Import/Export Standardı

### Default Export
- Her dosyada tek bir default export olmalı
- Component veya class'lar için kullanın

```javascript
// Doğru
export default class UserManager {
    // ...
}

// Doğru
export default {
    init() {
        // ...
    }
};
```

### Named Export
- Utility fonksiyonları ve sabitler için kullanın

```javascript
// Doğru
export const API_URL = '/api/v1';
export function formatDate(date) {
    // ...
}
```

## JSDoc Standardı

### Class Documentation
```javascript
/**
 * Kullanıcı yönetimi için temel sınıf
 * @class UserManager
 * @param {Object} options - Yapılandırma seçenekleri
 * @param {string} options.apiUrl - API endpoint URL'i
 * @param {number} options.timeout - İstek timeout süresi
 */
class UserManager {
    constructor(options = {}) {
        // ...
    }
}
```

### Method Documentation
```javascript
/**
 * Kullanıcı verilerini getirir
 * @async
 * @param {number} userId - Kullanıcı ID'si
 * @returns {Promise<Object>} Kullanıcı verileri
 * @throws {Error} API hatası durumunda
 */
async getUserData(userId) {
    // ...
}
```

### Function Documentation
```javascript
/**
 * Para birimi formatlar
 * @param {number} amount - Miktar
 * @param {string} [currency='TRY'] - Para birimi kodu
 * @returns {string} Formatlanmış para birimi
 * @example
 * formatCurrency(1234.56) // "₺1.234,56"
 * formatCurrency(1234.56, 'USD') // "$1,234.56"
 */
function formatCurrency(amount, currency = 'TRY') {
    // ...
}
```

## Type Definitions

### @typedef kullanımı
```javascript
/**
 * @typedef {Object} User
 * @property {number} id - Kullanıcı ID'si
 * @property {string} name - Kullanıcı adı
 * @property {string} email - E-posta adresi
 * @property {Date} createdAt - Oluşturulma tarihi
 */

/**
 * @param {User} user - Kullanıcı nesnesi
 */
function processUser(user) {
    // ...
}
```

## Event Naming

### Custom Events
- Lowercase ve hyphen kullanın
- Namespace ile prefix ekleyin
- Örnek: `vivacrm:user-updated`, `vivacrm:order-created`

```javascript
// Event dispatch
document.dispatchEvent(new CustomEvent('vivacrm:user-updated', {
    detail: { userId: 123 }
}));

// Event listening
document.addEventListener('vivacrm:user-updated', (event) => {
    console.log('User updated:', event.detail.userId);
});
```

## Error Handling

### Error Classes
```javascript
/**
 * API hatası için özel error sınıfı
 * @extends Error
 */
class ApiError extends Error {
    /**
     * @param {string} message - Hata mesajı
     * @param {number} statusCode - HTTP durum kodu
     * @param {Object} data - Ek hata verileri
     */
    constructor(message, statusCode, data = {}) {
        super(message);
        this.name = 'ApiError';
        this.statusCode = statusCode;
        this.data = data;
    }
}
```

## Best Practices

### 1. Açıklayıcı İsimler
```javascript
// Kötü
const d = new Date();
const u = users.filter(u => u.active);

// İyi
const currentDate = new Date();
const activeUsers = users.filter(user => user.active);
```

### 2. Boolean İsimlendirme
```javascript
// Kötü
const loading = true;
const visible = false;

// İyi
const isLoading = true;
const isVisible = false;
const hasError = false;
const canEdit = true;
```

### 3. Action-Based Method İsimleri
```javascript
// Kötü
userUpdate() { }
dataProcess() { }

// İyi
updateUser() { }
processData() { }
fetchOrders() { }
handleSubmit() { }
```

### 4. Consistency
Aynı konsept için her zaman aynı isimlendirmeyi kullanın:
- `fetch*` - Veri çekme işlemleri
- `handle*` - Event handler'lar
- `process*` - Veri işleme
- `validate*` - Doğrulama işlemleri
- `format*` - Formatlama işlemleri