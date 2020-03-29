import os
import sys
import configparser
import boto3


from django.conf import settings
import logging

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('productscraper')


# object = s3.Object('bucket_name','key')
config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath('..'), 'utilities', 'properties.ini'))

class AWSHandler():
    def __init__(self, bucket_name, key):
        self.bucket = bucket_name
        self.key = key
        self.s3resource = boto3.resource('s3', endpoint_url='https://s3.us-west-2.amazonaws.com/')



    @property
    def s3object(self):
        if self.bucket and self.key:
            logger.info("S3 object is ")
            s3object_ = self.s3resource.Object(self.bucket,self.key)
            logger.info("S3 object is ",s3object_)
            return s3object_

        else:
            logger.error("Value Error! Either key or bucket is not specified")
            raise("Value Error! Either key or bucket is not specified")
            return

    def getMetadata(self):
        return self.s3object.metadata


if __name__ == '__main__':
	p1 = 'product-scraper-oregon-qa-mi-daci'
	p2 = 'amazon__B000J130TS__v2'

	awshndl = AWSHandler(p1,p2)
	print(awshndl.getMetadata())
