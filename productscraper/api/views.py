
import requests
import urllib
import json
import snowflake.connector
from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework.parsers import JSONParser
from .serializers import (ProductSerializer,
                          FetchSkuSerializer,
                          FetchMetadataSerializer)
from ..productDetails import ProductDetails
from ..utilities.db_manager import DBManager
from ..handlers.awshandler import AWSHandler

from django.conf import settings
import logging

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('productscraper')


class ProductScraperAPIView(APIView, ProductDetails):
    ''' Product Scraper Response for single request
        It will accept a site, sku or url, SCP, pdp_cache, browser and env
        as form input and return a json response indicating the summary and the
        issues found in the scraper response.
        Sample Curl:
        curl -d "site=homedepot&sku=202204204&env=prod" http://sctt-backend.boomlowes.com/api/productScraper/
    '''
    permission_classes      = []
    authentication_classes  = []
    # def __init__(self, arg):
    #     super(ProductScraperAPIView, self).__init__()
    #     self.arg = arg


    def post(self, request, format=None, *args, **kwargs):
        site                    = request.POST.get('site')
        sku                     = request.POST.get('sku')
        url                     = request.POST.get('url')
        scraperConsumerParams   = request.POST.get('scraperConsumerParams')
        pdp_cache               = request.POST.get('pdp_cache')
        browser                 = request.POST.get('browser')
        env                     = request.POST.get('env')
        stack                   = request.POST.get('stack')

        if url:
            url = urllib.parse.quote_plus(url)
        context = self.getProductDetails(site, sku, url, scraperConsumerParams, pdp_cache, browser, env, stack)
        serializer = ProductSerializer(context)
        return Response(serializer.data)

class ProductScraperListAPIView(APIView, ProductDetails):
    ''' Product Scraper Response for bulk request
        It will accept a site, list of skus, SCP, pdp_cache, browser and env
        as form input and return an array of json responses
        Sample Curl:
        curl -d "site=homedepot&skulist=202204204,301382945&env=prod" http://sctt-backend.boomlowes.com/api/productScraper/list/
    '''
    permission_classes      = []
    authentication_classes  = []

    def post(self, request, format=None, *args, **kwargs):
        site                    = request.POST.get('site')
        skulist                 = request.POST.get('skulist')
        scraperConsumerParams   = request.POST.get('scraperConsumerParams')
        pdp_cache               = request.POST.get('pdp_cache')
        browser                 = request.POST.get('browser')
        env                     = request.POST.get('env')
        stack                   = request.POST.get('stack')
        url                     = None

        responseList = []
        for sku in skulist.split(','):
            context = self.getProductDetails(site, sku, url, scraperConsumerParams, pdp_cache, browser, env, stack)
            serializer = ProductSerializer(context)
            responseList.append((serializer.data))

        return Response(responseList)

class FetchSkuAPIView(APIView):
    ''' Response to fetch skus from cm.competition table.
    Input provided should be either of these through a form :
    1. The client, comp_name, attribute_name on which the
    check is to be specified, attribute_value, feed_date and skuCount or,
    2. The entire snowflake query
    Sample Curl:
    curl -d "client=lowes&comp_name=homedepot.com&feed_date=2019-12-10&skuCount=100&attribute_name=sas_offer_price&attribute_value=not null"
    http://sctt-backend.boomlowes.com/api/productScraper/fetchSkus/
    '''
    permission_classes      = []
    authentication_classes  = []

    def post(self, request, *args, **kwargs):
        client          = request.POST.get('client')
        comp_name       = request.POST.get('comp_name')
        attribute       = request.POST.get('attribute_name')
        attribute_val   = request.POST.get('attribute_value')
        feed_date       = request.POST.get('feed_date')
        query           = request.POST.get('query')
        skuCount        = request.POST.get('skuCount')
        db_details      = DBManager(client).getDbCredential()

        connection      = snowflake.connector.connect(
                                user=db_details.get('username'),
                                password=db_details.get('password'),
                                account=db_details.get('account'),
                                )
        cursor = connection.cursor()
        if cursor:
            logger.info("Snowflake comnnection succesful")
        else:
            logger.error("Could not comnnect to snowflake")
        database        = db_details.get('db')
        warehouse       = db_details.get('warehouse')
        skus = []
        if attribute_val == "null" or attribute_val == "not null":
            comparator_ = "is"
        else:
            comparator_ = "="
        try:
            cursor.execute("use warehouse {}".format(warehouse))
            cursor.execute("use DATABASE {}".format(database))
            if not query:
                query = ("select distinct(comp_sku) from cm.competition where comp_name='{}' and {} {} {} and feed_date='{}' limit {};"
                            .format(comp_name,attribute,comparator_,attribute_val,feed_date,skuCount))

            cursor.execute(query)
            rows = cursor.fetchall()
            for sku in rows:
                skus.append(sku[0])

            context = {}
            context['skus'] = skus
            serializer = FetchSkuSerializer(context)
        except snowflake.connector.errors.ProgrammingError as e:
            logger.error(e)
            serializer = None

        finally:
            cursor.close()

        connection.close()
        return Response(serializer.data)

class FetchS3MetadataAPIView(APIView, AWSHandler):
    ''' Response to fetch metadata of a particular S3 Object.
    Input provided should be the name of the bucket to be accessed and the key.
    DO NOT append __v2 in the key.
    Sample Curl:
    curl -d "bucket_name=product-scraper-oregon-qa-mi-daci&key=amazon__B000J130TS" http://sctt-backend.boomlowes.com/api/productScraper/fetchS3Metadata/
    '''
    permission_classes      = []
    authentication_classes  = []

    def post(self, request, *args, **kwargs):
        bucket_name     = request.POST.get('bucket_name')
        key             = request.POST.get('key')


        if key:
            key = key+"__v2"
        logger.info("Requesting metadata")
        aws = AWSHandler(bucket_name,key)
        try:
            metadata = aws.getMetadata()
        except Exception as e:
            metadata = {}
            metadata['message'] = "Could not fetch metadata for the given key, make sure the key and the bucket is valid"
        # metadata = aws.getMetadata()
        # if not metadata:
        #     metadata =
        logger.info("Request succesful")
        logger.info("Metadata = {}".format(metadata))
        context = {}
        context['metadata'] = metadata
        serializer = FetchMetadataSerializer(context)
        return Response(serializer.data)
