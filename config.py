"""
Configuration file
"""
__author__ = 'Cesar'

import logging

# Logging
logging.basicConfig(format='%(asctime)s - [%(levelname)s]: %(message)s',
                    filename='/home/logs/ocr_helper.log',
                    level=logging.DEBUG)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("googleapiclient").setLevel(logging.WARNING)
logging.getLogger("oauth2client").setLevel(logging.WARNING)

BUCKET = 'ocr-test-pics'
BUCKET_CROPPED = 'ocr-test-pics-cropped'

QUEUE = 'need-help-queue'
