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

# Images
BUCKET = 'ocr-test-pics'
BUCKET_CROPPED = 'ocr-test-pics-cropped'

# Task queues
QUEUE = 'need-help-queue'
READING_LEASE_TIME = 60
TRAINING_LEASE_TIME = 60*5
CROPPING_LEASE_TIME = 60*3

