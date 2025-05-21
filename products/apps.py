from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    verbose_name = 'Ürünler'
    
    def ready(self):
        """
        Uygulama başladığında signals'ı import et.
        Bu, signal handler'ların kaydedilmesini sağlar.
        """
        # Import signals to register handlers
        from . import signals