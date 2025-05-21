from django.urls import path
from .views import ExcelUploadHistoryAPIView

app_name = 'core_api'

urlpatterns = [
    path('excel/upload-history/', ExcelUploadHistoryAPIView.as_view(), name='excel-upload-history'),
]