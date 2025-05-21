/**
 * Register Form Component - VivaCRM
 * 
 * Kullanıcı kayıt formu işlevselliği
 */

export default function registerForm() {
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
}