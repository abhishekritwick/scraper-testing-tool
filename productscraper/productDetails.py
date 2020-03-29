import requests
import json
from django.conf import settings
import logging

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('productscraper')


class ProductDetails(object):

    def getProductDetails(self, retailer, sku, url, scp, pdp_cache, browser, env, stack):
        context = {}
        if not stack:
            stack = "oregon"

        prefix = ""
        if env and env == "prod":
            prefix = ""
        elif env:
            prefix = env + "."

        summary = []
        if not(stack!= 'oregon' and env == 'prod'):

            if sku:
                scraperUrl = "http://"+prefix+stack+".scraper.boomlowes.com/product-scraper/getProductDetails?site=%s&sku=%s" %(retailer,sku)
            elif url:
                scraperUrl = "http://"+prefix+stack+".scraper.boomlowes.com/product-scraper/getProductDetails?site=%s&url=%s" %(retailer,url)

            if scp and scp!= 'enumerate':
                scraperUrl += '&scraperConsumerParams=%s' %(scp)
            elif scp:
                scraperUrl += '&enumerate=true'

            if pdp_cache:
                scraperUrl += '&pdpCache=%s' %(pdp_cache)

            if browser:
                scraperUrl += '&browser=%s' %(browser)

            logger.info("Requesting url :",scraperUrl)
            response = requests.get(scraperUrl)
            dataobj = {}
            issues = None


            if response.status_code == 200:
                jsondata = response.json()
                summary,issues = self.getSummary(jsondata)
                cachekey = jsondata['cacheKey']

                if not cachekey:
                    cacheKeyPrefix = retailer.replace(".","")
                    cacheKeyPrefix = cacheKeyPrefix.replace("com","")
                    cachekey = cacheKeyPrefix + "__" + sku

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
                logger.error("The {} machine seems to be down".format(env))
            else:
                data_test = None
                if 'not implemented' in response.text:
                    summary.append("The site is not implemented")
                    logger.error("The site is not implemented")
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
        context['sku'] = sku
        context['url'] = url
        context['summary'] = summary
        context['issues'] = issues
        context['scraperApi'] = scraperUrl
        return context

    def getSummary(self,jsondata):
        try:
            logger.info("Generating Summary for product scraper response")
            rules = []
            issues = []
            scrapeDate = None
            try:
                time = jsondata.get('scrapeDate')
                time = int(str(time)[0:-3])
                scrapeDate = datetime.datetime.utcfromtimestamp(time).strftime('%c')
            except:
                pass
            if scrapeDate:
                rules.append("Scrape Date = "+str(scrapeDate))
            pageType = jsondata.get('pageType')
            rules.append("Page Type = "+str(pageType))
            scraper_status = jsondata['scraperStatus']
            rules.append("Scraper Status = "+str(scraper_status))
            if jsondata.get('product'):
                title = jsondata['product']['title']
                if not title:
                    issues.append("Title is null")

                brand = jsondata['product']['brand']
                if not brand:
                    issues.append('Brand is not getting captured')
                belowMap = jsondata['product']['isBelowMAP']
                offerPrice = jsondata['product']['offerPrice']
                minofferPrice = jsondata['product']['minOfferPrice']
                maxofferPrice = jsondata['product']['maxOfferPrice']
                sellerName = None
                if jsondata['product'].get('primarySeller'):
                    if jsondata['product'].get('primarySeller').get('sellerMetaInfo'):
                        sellerName = jsondata['product'].get('primarySeller').get('sellerMetaInfo').get('sellerName')

                if not (offerPrice or (minofferPrice and maxofferPrice)):
                    issues.append("Offer Price is not getting captured")
                else:
                    if not sellerName:
                        issues.append("Seller Name is not getting captured")
                    if belowMap:
                        issues.append("BelowMAP getting captured wrongly")
                listPrice = jsondata['product']['listPrice']
                if listPrice and  listPrice < offerPrice:
                    issues.append("List Price is less than offer price")

                site = jsondata['site']
                productUrl = jsondata['product']['productUrl']
                if site not in productUrl:
                    issues.append("Product URL not belonging to comp website")

                # scraper_status in ('No price information available.', '10004', 'Out of Stock')
                avail_list = ('in stock','instock','available now','available from these sellers','available online only')
                scraper_status = jsondata['scraperStatus']
                availability = jsondata['product']['optionalFields']['availability']
                instock = jsondata['product']['inStock']
                if scraper_status in ('No price information available.', '10004', 'Out of Stock'):
                    item = [item for item in avail_list if item in availability]
                    if item:
                        issues.append('Scraper status and Availability mismatch')

                if availability and scraper_status == 'Page not Found':
                    issues.append('Scraper status and Availability mismatch')

                review_count = jsondata['product']['customerReviewsCount']
                avg_rating = jsondata['product']['avgRating']
                if review_count and review_count >= 10 and not avg_rating:
                    issues.append('Invalid Reviews & Ratings')

                if avg_rating and avg_rating > 0 and not review_count:
                    issues.append('Missing product review count')


                variations = jsondata['product']['variations']
                totalVariation = len(variations)
                rules.append("Number of variations = "+str(totalVariation))
                variationDict = {}
                variationNameMap = {}
                hasVariations = jsondata['product']['hasVariations']
                rules.append("Has Variations = "+str(hasVariations))
                variants = {}
                if hasVariations:
                    if variations:

                        variantCount = 0
                        for variation in variations:
                            variantDict = {}
                            variationName = variation['variationName']

                            scrapedVariationName = variation['scrapedVariationName']
                            if variationName:
                                variationName = variationName.lower()
                            variationNameMap[scrapedVariationName] = variationName
                            variantDict['scrapedVariationName'] = scrapedVariationName
                            variationCount = len(variation['allVariations'])
                            variationList = []
                            i = 0

                            while i < variationCount:
                                variationList.append(variation['allVariations'][i]['value'])
                                i += 1

                            variantDict['values'] = variationList
                            variationDict[variationName] = variantDict
                            variants[variationName] = str(variationCount) + ' items'
                        var_info = {'Variation Information':json.dumps(variants)}
                        rules.append(var_info)

                    else:
                        issues.append('HasVariations is true and Variations are not getting captured')

                else:
                    if variations:
                        issues.append('HasVariations is false and Variations are getting captured')

                v = list(variationDict.values())
                scrapedVariationNameList = [v[i]['scrapedVariationName'] for i in range(len(variationDict))]
                scrapedVariationNameList.sort()
                vcs = jsondata['product']['variantsContainer']
                if hasVariations:
                    if vcs:
                        rules.append('Total VCs = ' + str(len(vcs)))
                        variantSet = set()
                        variantApiSet = set()
                        vc_count = 0
                        for vc in vcs:
                            vc_count += 1
                            if vc['variants']:
                                v2 = vc['variants'].keys()
                                variantKeys = list(v2)
                                variantKeys.sort()
                                zipper = zip(scrapedVariationNameList, variantKeys)
                                for index in zipper:
                                    if index[0] != index[1]:
                                        issues.append('Variation Missing in Free Flowing VC ' + str(vc_count))


                                itemList = []
                                for item in vc['variants'].items():
                                    if item[1] not in variationDict[variationNameMap[item[0]]]['values']:
                                        issues.append('Variant name mismatch in Variations and Free Flowing VC facet')
                                    if item[1]:
                                        itemList.append(item[1])
                                if tuple(itemList) in variantSet and len(vcs) > 1:
                                    issues.append('Duplicate values getting captured in Free Flowing VCs')
                                else:
                                    variantSet.add(tuple(itemList))


                            elif vc['variantApiRequest']:
                                variantKeys = [item[0] for item in vc['variantApiRequest'].items() if item[1]]
                                variantKeys.sort()
                                zipper = zip(variationDict.keys(), variantKeys)
                                for index in zipper:
                                    if index[0].lower() != index[1].lower():
                                        issues.append('Variation Missing in Non Free Flowing VC ' + str(vc_count))
                                itemList = []
                                for item in vc['variantApiRequest'].items():
                                    if variationDict.get(item[0].lower(),None):
                                        if item[1] and item[1] not in variationDict[item[0].lower()]['values']:
                                            issues.append('Variant name mismatch in Variations and Non Free Flowing VC facet')
                                        if item[1]:
                                            itemList.append(item[1])
                                if tuple(itemList) in variantApiSet and len(vcs) > 1:
                                    issues.append('Duplicate values getting captured in Non Free Flowing VCs')
                                else:
                                    variantApiSet.add(tuple(itemList))

            logger.info("Summary generated for product scraper")
            return (rules,issues)
        except KeyError as e:
            logger.error("No key found ",e)
            raise e("No key found")
