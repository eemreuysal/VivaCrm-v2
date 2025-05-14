// Main JavaScript file for VivaCRM v2
document.addEventListener('DOMContentLoaded', function() {
  initializeApp();
});

function initializeApp() {
  setupHtmxExtensions();
  setupThemeToggle();
  setupAlpineComponents();
  setupEventListeners();
}

// HTMX Extensions and Settings
function setupHtmxExtensions() {
  // Load HTMX extensions if needed
  if (typeof htmx !== 'undefined') {
    // Set HTMX global configurations
    htmx.config.useTemplateFragments = true;
    htmx.config.allowEval = false;
    htmx.config.historyCacheSize = 10;
    
    // Add HTMX global events
    document.body.addEventListener('htmx:configRequest', function(event) {
      // Add CSRF token to all HTMX requests
      event.detail.headers['X-CSRFToken'] = getCsrfToken();
    });
    
    document.body.addEventListener('htmx:afterSwap', function(event) {
      // Reinitialize any JS components that need it after HTMX content swap
      reinitializeComponents();
    });
    
    document.body.addEventListener('htmx:responseError', function(event) {
      // Show error message when HTMX requests fail
      showToast('Bir hata oluştu. Lütfen tekrar deneyin.', 'error');
    });
  }
}

// Theme Toggle
function setupThemeToggle() {
  // Theme toggle if present
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'vivacrm' ? 'vivacrmDark' : 'vivacrm';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('vivacrm-theme', newTheme);
    });
  }
  
  // Apply saved theme from localStorage if any, default to light theme
  const savedTheme = localStorage.getItem('vivacrm-theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  } else {
    // Set default theme to light theme (vivacrm)
    document.documentElement.setAttribute('data-theme', 'vivacrm');
    localStorage.setItem('vivacrm-theme', 'vivacrm');
  }
}

// Alpine.js Components
function setupAlpineComponents() {
  if (typeof Alpine !== 'undefined') {
    // Register Alpine.js components and stores
    Alpine.store('app', {
      sidebarOpen: false,
      toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
      }
    });
    
    Alpine.data('dropdown', () => ({
      open: false,
      toggle() {
        this.open = !this.open;
      },
      close() {
        this.open = false;
      }
    }));
    
    Alpine.data('modal', () => ({
      visible: false,
      show() {
        this.visible = true;
        document.body.classList.add('overflow-hidden');
      },
      hide() {
        this.visible = false;
        document.body.classList.remove('overflow-hidden');
      }
    }));
    
    // Add more Alpine.js components as needed
  }
}

// General Event Listeners
function setupEventListeners() {
  // Close dropdown menus when clicking outside
  document.addEventListener('click', function(event) {
    const dropdowns = document.querySelectorAll('.dropdown.dropdown-open');
    dropdowns.forEach(function(dropdown) {
      if (!dropdown.contains(event.target)) {
        dropdown.classList.remove('dropdown-open');
      }
    });
  });
  
  // Setup form enhancements
  setupFormEnhancements();
}

// Form Enhancements
function setupFormEnhancements() {
  // Auto-resize textareas
  document.querySelectorAll('textarea[data-autoresize]').forEach(function(textarea) {
    textarea.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });
    // Initial resize
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
  });
  
  // Add confirmation to delete forms
  document.querySelectorAll('form[data-confirm]').forEach(function(form) {
    form.addEventListener('submit', function(event) {
      const confirmMessage = this.getAttribute('data-confirm') || 'Bu işlemi gerçekleştirmek istediğinize emin misiniz?';
      if (!confirm(confirmMessage)) {
        event.preventDefault();
      }
    });
  });
}

// Helper Functions
function showToast(message, type = 'info') {
  // Implementation depends on your toast library
  if (typeof Toastify !== 'undefined') {
    Toastify({
      text: message,
      duration: 3000,
      gravity: "top",
      position: "right",
      className: `toast-${type}`
    }).showToast();
  } else {
    console.log(`Toast (${type}): ${message}`);
  }
}

function getCsrfToken() {
  // Get CSRF token from cookie
  return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
}

function reinitializeComponents() {
  // Reinitialize components after HTMX content swap
  if (typeof Alpine !== 'undefined') {
    Alpine.initTree(document.body);
  }
  
  // Re-initialize any other JS components here
}

// Export any needed functions for other modules to use
window.vivacrm = {
  showToast,
  reinitializeComponents
};