from django.conf.urls import url
from .views import (ProductScraperAPIView,
                    ProductScraperListAPIView,
                    FetchSkuAPIView,
                    FetchS3MetadataAPIView)

urlpatterns = [
    url(r'^$', ProductScraperAPIView.as_view()),
    url(r'^list/', ProductScraperListAPIView.as_view()),
    url(r'^fetchSkus/', FetchSkuAPIView.as_view()),
    url(r'^fetchS3Metadata/', FetchS3MetadataAPIView.as_view()),
]


# /productScraper/dummy/
