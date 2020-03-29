from django.conf.urls import url
from .views import SearchScraperAPIView

urlpatterns = [
    url(r'^$', SearchScraperAPIView.as_view()),
    # url(r'^list/', ProductScraperListAPIView.as_view()),
    # url(r'^fetchSkus/', FetchSkuAPIView.as_view()),
]
