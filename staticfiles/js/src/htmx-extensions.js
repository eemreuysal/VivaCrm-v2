// HTMX Extensions for VivaCRM v2

// Load Indicator Extension
htmx.defineExtension('load-indicator', {
  onEvent: function(name, evt) {
    if (name === 'htmx:beforeRequest') {
      const target = evt.detail.elt;
      const indicator = target.querySelector('.htmx-indicator') || target.closest('[data-indicator]');
      
      if (indicator) {
        indicator.classList.add('active');
        evt.detail.xhr.addEventListener('loadend', function() {
          setTimeout(() => {
            indicator.classList.remove('active');
          }, 200);
        });
      }
    }
  }
});

// CSRF Extension (for Django)
htmx.defineExtension('csrf', {
  onEvent: function(name, evt) {
    if (name === 'htmx:configRequest') {
      const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
      if (csrfToken) {
        evt.detail.headers['X-CSRFToken'] = csrfToken;
      }
    }
  }
});

// Confirm Extension (for delete and other destructive actions)
htmx.defineExtension('confirm', {
  onEvent: function(name, evt) {
    if (name === 'htmx:beforeRequest') {
      const target = evt.detail.elt;
      const confirmMessage = target.getAttribute('data-confirm');
      
      if (confirmMessage && !window.confirm(confirmMessage)) {
        evt.detail.preventDefault();
      }
    }
  }
});

// Toast Extension (for showing messages after actions)
htmx.defineExtension('toast', {
  onEvent: function(name, evt) {
    if (name === 'htmx:afterRequest') {
      const xhr = evt.detail.xhr;
      
      // Check for toast header
      const toastMessage = xhr.getResponseHeader('HX-Trigger-Toast-Message');
      const toastType = xhr.getResponseHeader('HX-Trigger-Toast-Type') || 'info';
      
      if (toastMessage) {
        showToast(toastMessage, toastType);
      }
    }
  }
});

// Infinite Scroll Extension
htmx.defineExtension('infinite-scroll', {
  onEvent: function(name, evt) {
    if (name === 'htmx:load') {
      document.querySelectorAll('[data-infinite-scroll]').forEach(function(el) {
        const targetSelector = el.getAttribute('data-infinite-scroll-target');
        const target = document.querySelector(targetSelector);
        
        if (target) {
          const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
              if (entry.isIntersecting && !target.getAttribute('data-loading')) {
                target.setAttribute('data-loading', 'true');
                htmx.trigger(target, 'load-more');
              }
            });
          }, { threshold: 0.1 });
          
          observer.observe(el);
        }
      });
    }
  }
});

// Theme Persistence Extension
htmx.defineExtension('theme-persistence', {
  onEvent: function(name, evt) {
    if (name === 'htmx:load') {
      const savedTheme = localStorage.getItem('vivacrm-theme');
      if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
      }
      
      // Theme toggle buttons
      document.querySelectorAll('[data-theme-toggle]').forEach(function(el) {
        el.addEventListener('click', function() {
          const currentTheme = document.documentElement.getAttribute('data-theme');
          const newTheme = currentTheme === 'vivacrm' ? 'vivacrmDark' : 'vivacrm';
          
          document.documentElement.setAttribute('data-theme', newTheme);
          localStorage.setItem('vivacrm-theme', newTheme);
        });
      });
    }
  }
});

// Form Validation Extension
htmx.defineExtension('form-validation', {
  onEvent: function(name, evt) {
    if (name === 'htmx:beforeRequest') {
      const form = evt.detail.elt.closest('form');
      
      if (form && form.getAttribute('data-validate') !== null) {
        if (!form.checkValidity()) {
          evt.detail.preventDefault();
          
          // Show validation messages
          form.classList.add('was-validated');
          
          // Focus first invalid field
          const firstInvalid = form.querySelector(':invalid');
          if (firstInvalid) {
            firstInvalid.focus();
          }
        }
      }
    }
  }
});

// Helper Functions
function showToast(message, type = 'info') {
  // Check if we have a toast container, if not create one
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2';
    document.body.appendChild(toastContainer);
  }
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} shadow-lg max-w-sm`;
  toast.innerHTML = `
    <div>
      <span>${message}</span>
    </div>
    <button class="btn btn-sm btn-ghost">×</button>
  `;
  
  // Add to container
  toastContainer.appendChild(toast);
  
  // Auto dismiss after 3 seconds
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, 3000);
  
  // Dismiss on click
  toast.querySelector('button').addEventListener('click', () => {
    toast.remove();
  });
}

// Initialize extensions
document.addEventListener('DOMContentLoaded', function() {
  htmx.config.useTemplateFragments = true;
  htmx.config.allowEval = false;
  htmx.config.historyCacheSize = 10;
  
  // Add extensions
  htmx.addExtension('load-indicator');
  htmx.addExtension('csrf');
  htmx.addExtension('confirm');
  htmx.addExtension('toast');
  htmx.addExtension('infinite-scroll');
  htmx.addExtension('theme-persistence');
  htmx.addExtension('form-validation');
});