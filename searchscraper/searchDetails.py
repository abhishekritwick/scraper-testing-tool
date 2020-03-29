import requests
import json
from django.conf import settings
import logging

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('searchscraper')
# print(settings.LOGGING)
# logging.config.dictConfig({
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'console': {
#             'format': '%(name)-12s %(levelname)-8s %(message)s'
#         },
#         'file': {
#             'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
#         }
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'console'
#         },
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'formatter': 'file',
#             'filename': 'test-log-file.log'
#         }
#     },
#     'loggers': {
#         '': {
#             'level': 'DEBUG',
#             'handlers': ['console', 'file']
#         }
#     }
# })



# '''
# {
# 'version': 1,
# 'disable_existing_loggers': False,
# 'formatters': {
#         'console': {
#             'format': '%(name)-12s %(levelname)-8s %(message)s'
#             },
#         'file': {
#             'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
#             }
#         },
#  'handlers': {
#         'file': {
#             'level': 'DEBUG',
#              'class': 'logging.FileHandler',
#              'formatter': 'file',
#              'filename': 'test-log-file.log'
#          },
#          'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'console'
#         }
#     },
# 'loggers': {
#         'django': {
#             'handlers': ['file'],
#             'level': 'DEBUG',
#             'propagate': True
#             }
#         }
# }
# '''

class SearchDetails(object):

    def getSearchDetails(self, retailer, search, url, cache, browser, env, stack):
        # print(settings.LOGGING)
        print("Done")
        logger.info("In getSearch Details")
        context = {}
        if not stack:
            stack = "oregon"

        summary = []
        prefix = ""
        if env and env == "prod":
            prefix = ""
        elif env:
            prefix = env + "."

        if not(stack!= 'oregon' and env == 'prod'):

            if search:
                scraperUrl = "http://"+prefix+stack+".scraper.boomlowes.com/product-scraper/getSearchResults?site=%s&search=%s" %(retailer,search)
            elif url:
                scraperUrl = "http://"+prefix+stack+".scraper.boomlowes.com/product-scraper/getSearchResults?site=%s&url=%s" %(retailer,url)

            if cache:
                scraperUrl += '&cache=%s' %(cache)

            if browser:
                scraperUrl += '&browser=%s' %(browser)

            response = requests.get(scraperUrl)
            dataobj = {}
            issues = None


            if response.status_code == 200:
                jsondata = response.json()
                summary,issues = self.getSummary(jsondata)
                cachekey = jsondata['cacheKey']

                if not cachekey:
                    cachedKeyUrl = None
                    dataobj['cachedKeyUrl'] = None
                    cachedVersionsUrl = None
                    dataobj['cachedVersionsUrl'] = None
                    cachedPagesPrefixUrl = None
                    dataobj['cachedPagesPrefixUrl'] = None

                if cachekey:
                    cachedKeyUrl = "http://"+prefix+"oregon.scraper.boomlowes.com/product-scraper/getCachedHtml?key=" + cachekey
                    dataobj['cachedKeyUrl'] = cachedKeyUrl
                    cachedVersionsUrl = "http://"+prefix+"oregon.scraper.boomlowes.com/product-scraper/getCachedVersionsByKey?key=" + cachekey
                    dataobj['cachedVersionsUrl'] = cachedVersionsUrl
                    cachedPagesPrefixUrl = "http://"+prefix+"oregon.scraper.boomlowes.com/product-scraper/getCachedPagesByPrefix?prefix=" + cachekey
                    dataobj['cachedPagesPrefixUrl'] = cachedPagesPrefixUrl




            elif response.status_code == 503:
                data_test = None
                summary = "The " + env + " machine seems to be down. Please up it and try again"
            else:
                data_test = None
                if 'not implemented' in response.text:
                    summary.append("Could not parse the response ",response.text)
                    summary.append("The site is not implemented")
                else:
                    summary = None

        else:
            summary.append("Invalid stack/environment combination, please make sure it is correct")
            dataobj = None
            issues  = None
            scraperUrl = None

        context['cacheURLs'] = dataobj
        context['env'] = env
        context['site'] = retailer
        context['url'] = url
        context['search'] = search
        context['summary'] = summary
        context['issues'] = issues
        context['scraperApi'] = scraperUrl
        return context

    def getSummary(self,jsondata):
        try:
            # logging.error("Generating Summary for scraper response in method getSummary")
            print("Break!!")
            logging.info("Generating Summary for scraper response in method getSummary")
            summary = []
            issues = []
            scrapeDate = None
            try:
                time = jsondata.get('scrapeDate')
                time = int(str(time)[0:-3])
                scrapeDate = datetime.datetime.utcfromtimestamp(time).strftime('%c')
            except:
                pass

            if scrapeDate:
                summary.append("Scrape Date = "+str(scrapeDate))

            pageType = jsondata.get('pageType')
            if pageType != 'SEARCH_PAGE' and pageType != 'PRODUCT_PAGE':
                issues.append("Page Type = "+str(pageType))
            else:
                summary.append("Page Type = "+str(pageType))
            urlCount = searchResultsCount = 0
            productUrls = jsondata.get('productUrls')
            searchResults = jsondata.get('searchResults')
            if productUrls:
                urlCount = len(jsondata['productUrls'])
            if searchResults:
                searchResultsCount = len(jsondata['productUrls'])

            if urlCount > searchResultsCount:
                diff = urlCount - searchResultsCount
                issues.append("{} more urls captured than search results")
            elif urlCount < searchResultsCount:
                diff = searchResultsCount - urlCount
                issues.append("{} less urls captured than search results")


            if None in productUrls:
                issues.append("Null value getting captured in urls")

            for searchresult_ in searchResults:
                sku = searchresult_["sku"]
                attribute_list = ["productUrl","title","brand","modelNumber","imageUrl","offerPrice","customerReviewsCount","avgRating"]
                null_list = [item for item in attribute_list if searchresult_['{}'.format(item)] is None]
                for attr_ in null_list:
                    issues.append('{} is captured null for sku : {}'.format(attr_,sku))

            return (summary,issues)
        except KeyError as e:
            # logger.error("No key found")
            raise e("No key found")
