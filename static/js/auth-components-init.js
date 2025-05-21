/**
 * Authentication Components Initialization for VivaCRM
 * 
 * Bu dosya, login ve register formları için Alpine.js bileşenlerini yüklemek 
 * ve kaydetmek için kullanılır.
 */

// Log fonksiyonu
function log(message, type = 'info') {
  const prefix = '🔐 Auth Components: ';
  
  switch(type) {
    case 'error':
      console.error(prefix + message);
      break;
    case 'warn':
      console.warn(prefix + message);
      break;
    default:
      console.log(prefix + message);
  }
}

// Kimlik doğrulama bileşenlerini global olarak tanımla
document.addEventListener('DOMContentLoaded', function() {
  log('Auth components initializing...');
  
  if (!window.Alpine) {
    log('Alpine.js not available. Auth components could not be registered.', 'error');
    return;
  }

  // Login Form bileşenini tanımla
  window.loginForm = function() {
    return {
      formData: {
        username: '',
        password: '',
        remember: false
      },
      showPassword: false,
      isSubmitting: false,
      errorMessage: '',
      errors: {},
      
      init() {
        log('Login form initialized');
        // Varsa URL'den hata parametrelerini analiz et
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('error')) {
          this.errorMessage = decodeURIComponent(urlParams.get('error'));
        }
      },
      
      // Form gönderme işlemi
      submitForm() {
        this.isSubmitting = true;
        this.errorMessage = '';
        this.errors = {};
        
        log('Submitting login form...');
        
        // Form verilerini hazırla
        const form = new FormData();
        form.append('username', this.formData.username);
        form.append('password', this.formData.password);
        if (this.formData.remember) {
          form.append('remember', 'on');
        }
        form.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        // Fetch API ile form gönder
        fetch(window.location.href, {
          method: 'POST',
          body: form,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(response => {
          if (response.redirected) {
            // Başarılı giriş, yönlendirme URL'sine git
            window.location.href = response.url;
            return;
          }
          
          if (response.headers.get('content-type')?.includes('application/json')) {
            // JSON yanıtını parse et
            return response.json().then(data => {
              // Hata durumunda
              if (data.errors) {
                this.errors = data.errors;
              }
              
              if (data.error) {
                this.errorMessage = data.error;
              } else if (data.__all__) {
                // Django form genel hataları
                this.errorMessage = Array.isArray(data.__all__) ? data.__all__[0] : data.__all__;
              }
              
              // İşlem tamamlandı
              this.isSubmitting = false;
            });
          }
          
          // HTML yanıtı - normal form gönderimi
          // Form başarısız oldu, sayfa yeniden yüklenecek
          document.querySelector('form').submit();
        })
        .catch(error => {
          console.error('Login error:', error);
          this.errorMessage = 'Giriş sırasında bir hata oluştu. Lütfen tekrar deneyin.';
          this.isSubmitting = false;
        });
      },
      
      // Şifre görünürlüğünü değiştir
      togglePasswordVisibility() {
        this.showPassword = !this.showPassword;
      }
    };
  };

  // Register Form bileşenini tanımla
  window.registerForm = function() {
    return {
      formData: {
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        password1: '',
        password2: '',
        terms_accepted: false
      },
      showPassword1: false,
      showPassword2: false,
      isSubmitting: false,
      errorMessage: '',
      errors: {},
      
      init() {
        log('Register form initialized');
        // Varsa URL'den hata parametrelerini analiz et
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('error')) {
          this.errorMessage = decodeURIComponent(urlParams.get('error'));
        }
      },
      
      // Form gönderme işlemi
      submitForm() {
        if (!this.validateForm()) {
          return;
        }
        
        this.isSubmitting = true;
        this.errorMessage = '';
        this.errors = {};
        
        log('Submitting registration form...');
        
        // Form verilerini hazırla
        const form = new FormData();
        for (const key in this.formData) {
          if (key === 'terms_accepted' && this.formData[key]) {
            form.append(key, 'on');
          } else {
            form.append(key, this.formData[key]);
          }
        }
        form.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        // Fetch API ile form gönder
        fetch(window.location.href, {
          method: 'POST',
          body: form,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(response => {
          if (response.redirected) {
            // Başarılı kayıt, yönlendirme URL'sine git
            window.location.href = response.url;
            return;
          }
          
          if (response.headers.get('content-type')?.includes('application/json')) {
            // JSON yanıtını parse et
            return response.json().then(data => {
              // Hata durumunda
              if (data.errors) {
                this.errors = data.errors;
              }
              
              if (data.error) {
                this.errorMessage = data.error;
              } else if (data.__all__) {
                // Django form genel hataları
                this.errorMessage = Array.isArray(data.__all__) ? data.__all__[0] : data.__all__;
              }
              
              // İşlem tamamlandı
              this.isSubmitting = false;
            });
          }
          
          // HTML yanıtı - normal form gönderimi
          // Form başarısız oldu, sayfa yeniden yüklenecek
          document.querySelector('form').submit();
        })
        .catch(error => {
          console.error('Registration error:', error);
          this.errorMessage = 'Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.';
          this.isSubmitting = false;
        });
      },
      
      // Form doğrulama
      validateForm() {
        this.errors = {};
        let isValid = true;
        
        // Kullanıcı adı doğrulama
        if (!this.formData.username.trim()) {
          this.errors.username = 'Kullanıcı adı gereklidir';
          isValid = false;
        } else if (this.formData.username.length < 3) {
          this.errors.username = 'Kullanıcı adı en az 3 karakter olmalıdır';
          isValid = false;
        }
        
        // Email doğrulama
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!this.formData.email.trim()) {
          this.errors.email = 'E-posta adresi gereklidir';
          isValid = false;
        } else if (!emailRegex.test(this.formData.email)) {
          this.errors.email = 'Geçerli bir e-posta adresi giriniz';
          isValid = false;
        }
        
        // Ad ve soyad doğrulama (opsiyonel)
        if (this.formData.first_name.trim() && this.formData.first_name.length < 2) {
          this.errors.first_name = 'Ad en az 2 karakter olmalıdır';
          isValid = false;
        }
        
        if (this.formData.last_name.trim() && this.formData.last_name.length < 2) {
          this.errors.last_name = 'Soyad en az 2 karakter olmalıdır';
          isValid = false;
        }
        
        // Şifre doğrulama
        if (!this.formData.password1) {
          this.errors.password1 = 'Şifre gereklidir';
          isValid = false;
        } else if (this.formData.password1.length < 8) {
          this.errors.password1 = 'Şifre en az 8 karakter olmalıdır';
          isValid = false;
        }
        
        // Şifre eşleştirme doğrulama
        if (!this.formData.password2) {
          this.errors.password2 = 'Şifre onayı gereklidir';
          isValid = false;
        } else if (this.formData.password1 !== this.formData.password2) {
          this.errors.password2 = 'Şifreler eşleşmiyor';
          isValid = false;
        }
        
        // Şartlar ve koşullar onayı
        if (!this.formData.terms_accepted) {
          this.errors.terms_accepted = 'Şartları ve koşulları kabul etmelisiniz';
          isValid = false;
        }
        
        return isValid;
      },
      
      // Şifre görünürlüğünü değiştir
      togglePassword1Visibility() {
        this.showPassword1 = !this.showPassword1;
      },
      
      // Şifre onayı görünürlüğünü değiştir
      togglePassword2Visibility() {
        this.showPassword2 = !this.showPassword2;
      }
    };
  };

  // Alpine.js'e bileşenleri kaydet
  if (typeof Alpine.data === 'function') {
    Alpine.data('loginForm', window.loginForm);
    Alpine.data('registerForm', window.registerForm);
    log('Auth components registered with Alpine.js successfully');
  } else {
    log('Alpine.data method is not available. Ensure Alpine.js is properly loaded.', 'error');
  }
  
  // Kimlik doğrulama sayfasını tespit et ve temayı ayarla
  if (window.location.pathname.includes('/login') || window.location.pathname.includes('/register')) {
    // ThemeManager'a erişim fonksiyonu
    const getStandardThemeManager = () => {
      // İlk olarak VivaCRM.themeManager'ı kontrol et (tercih edilen)
      if (window.VivaCRM && window.VivaCRM.themeManager) {
        return window.VivaCRM.themeManager;
      }
      
      // Geriye dönük uyumluluk için vivaCRM.themeManager'ı da kontrol et
      if (window.vivaCRM && window.vivaCRM.themeManager) {
        return window.vivaCRM.themeManager;
      }
      
      return null;
    };
    
    // Öncelikle merkezi ThemeManager'ı kontrol et
    const themeManager = getStandardThemeManager();
    
    if (themeManager) {
      // ThemeManager aracılığıyla açık temaya zorla
      themeManager.setTheme('light', 'system');
      log('Theme set to light for auth pages using ThemeManager');
    } else if (typeof Alpine.store === 'function' && Alpine.store('theme')) {
      // ThemeManager yoksa Alpine.store aracılığıyla tema ayarla
      Alpine.store('theme').applyTheme('light');
      log('Theme set to light for auth pages using Alpine store');
    }
    
    // Tema geçiş butonlarını gizle
    const themeToggles = document.querySelectorAll('.theme-toggle-btn');
    themeToggles.forEach(toggle => {
      toggle.style.display = 'none';
    });
  }
});

// Global erişim için dışa aktar
window.AuthComponents = {
  loginForm: window.loginForm,
  registerForm: window.registerForm
};