import requests
import urllib
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from ..searchDetails import SearchDetails
from .serializers import SearchSerializer

from django.conf import settings
import logging

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('searchscraper')

class SearchScraperAPIView(APIView, SearchDetails):
    """ Search Scraper Response
        It will accept a site, search or url, cachge, browser and env
        as input and return a json response indicating the summary and the
        issues found in the scraper response.
        Sample Curl:
        curl -d "site=homedepot&search=curtains&env=prod" http://sctt-backend.boomlowes.com/api/searchScraper/
        """
    permission_classes      = []
    authentication_classes  = []

    def post(self, request, *args, **kwargs):
        site                    = request.POST.get('site')
        search                  = request.POST.get('search')
        url                     = request.POST.get('url')
        cache                   = request.POST.get('cache')
        browser                 = request.POST.get('browser')
        env                     = request.POST.get('env')
        stack                   = request.POST.get('stack')

        if url:
            url = urllib.parse.quote_plus(url)

        context = self.getSearchDetails(site, search, url, cache, browser, env, stack)
        serializer = SearchSerializer(context)
        return Response(serializer.data)
