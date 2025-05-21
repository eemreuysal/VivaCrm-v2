/**
 * Login Form Component - VivaCRM
 * 
 * Kimlik doğrulama için kullanıcı adı & şifre form işlevselliği
 */

export default function loginForm() {
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
}