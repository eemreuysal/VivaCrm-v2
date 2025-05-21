// Sidebar and theme controller for VivaCRM v2
document.addEventListener('alpine:init', () => {
  // Sidebar controller component
  Alpine.data('sidebarController', () => ({
    isSidebarCollapsed: localStorage.getItem('vivacrm-sidebar-collapsed') === 'true' || false,
    isMobileSidebarOpen: false,
    
    init() {
      // Watch for sidebar state changes and save to localStorage
      this.$watch('isSidebarCollapsed', value => {
        localStorage.setItem('vivacrm-sidebar-collapsed', value);
      });
      
      // Close mobile sidebar when clicking outside
      document.addEventListener('click', (event) => {
        if (this.isMobileSidebarOpen && 
            !this.$refs.mobileSidebar.contains(event.target) && 
            !this.$refs.mobileMenuButton.contains(event.target)) {
          this.isMobileSidebarOpen = false;
        }
      });
      
      // Auto hide/show navbar on scroll
      let lastScrollTop = 0;
      const navbar = document.querySelector('.navbar.sticky');
      
      if (navbar) {
        window.addEventListener('scroll', () => {
          let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
          if (scrollTop > lastScrollTop && scrollTop > 80) {
            // Scroll down - hide navbar
            navbar.style.transform = 'translateY(-100%)';
          } else {
            // Scroll up - show navbar
            navbar.style.transform = 'translateY(0)';
          }
          lastScrollTop = scrollTop;
        });
      }
    },
    
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed;
    },
    
    openMobileSidebar() {
      this.isMobileSidebarOpen = true;
    },
    
    closeMobileSidebar() {
      this.isMobileSidebarOpen = false;
    }
  }));
  
  // Theme controller component
  Alpine.data('themeController', () => ({
    darkMode: localStorage.getItem('vivacrm-theme') === 'vivacrmDark' || false,
    
    init() {
      // Apply theme on initial load
      document.documentElement.setAttribute('data-theme', this.darkMode ? 'vivacrmDark' : 'vivacrm');
      
      // Watch for theme changes and save to localStorage
      this.$watch('darkMode', value => {
        localStorage.setItem('vivacrm-theme', value ? 'vivacrmDark' : 'vivacrm');
        document.documentElement.setAttribute('data-theme', value ? 'vivacrmDark' : 'vivacrm');
      });
    },
    
    toggleTheme() {
      this.darkMode = !this.darkMode;
    }
  }));
  
  // Notification controller component
  Alpine.data('notification', () => ({
    visible: false,
    notifications: [
      {
        id: 1,
        title: 'Yeni Sipariş',
        message: 'Yeni bir sipariş oluşturuldu.',
        time: '5 dakika önce',
        read: false
      },
      {
        id: 2,
        title: 'Stok Uyarısı',
        message: 'Bazı ürünlerin stok seviyesi düşük.',
        time: '2 saat önce',
        read: false
      },
      {
        id: 3,
        title: 'Sistem Güncellemesi',
        message: 'Sistem başarıyla güncellendi.',
        time: '1 gün önce',
        read: true
      }
    ],
    
    get unreadCount() {
      return this.notifications.filter(n => !n.read).length;
    },
    
    toggle() {
      this.visible = !this.visible;
    },
    
    markAsRead(id) {
      const notification = this.notifications.find(n => n.id === id);
      if (notification) {
        notification.read = true;
      }
    },
    
    markAllAsRead() {
      this.notifications.forEach(n => {
        n.read = true;
      });
    }
  }));
});