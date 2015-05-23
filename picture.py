"""
Class that represents an picture containing the measurement of a sensor
"""
__author__ = 'Cesar'

import config
import googleapiclient.discovery as api_discovery
from googleapiclient.http import MediaFileUpload
from googleapiclient import errors
import httplib2
from StringIO import StringIO
import credentials
from PIL import Image


class Picture:

    pic = Image
    cropped = Image
    image_id = ''
    storage_api = None
    public_url_cropped = ''
    public_url_original = ''

    def __init__(self, image_id):
        """
        Image object constructor. Gets the image from the Cloud Store, also creates the object to interact with the
        storage_api.
            :param: image_id: the URLsafe Cloud Store identifier of the image provided by the user
            :return: A picture object of the region of interest image from the reading
        """
        http = httplib2.Http()
        c = credentials.get_credentials()
        if c:
            self.storage_api = api_discovery.build('storage', 'v1', http=c.authorize(http))
            request = self.storage_api.objects().get_media(bucket=config.BUCKET, object=image_id)
            resp = request.execute()
            self.pic = Image.open(StringIO(resp))
            self.image_id = image_id
            self.public_url_original = 'https://{0}.storage.googleapis.com/{1}'.format(config.BUCKET, self.image_id)
            self._extract_region_of_interest(save=False)
        else:
            config.logging.error('Error getting credentials')

    def _extract_region_of_interest(self, save=False):
        """
        Crops self.pic to extract the region of interest.
        Crop size is determined as a function of the image size, type of image (red, green, blue .. see CL photo app)
        and the relative size of the region of interest in both X and Y. It is also assumed that the region of interest
        is in the approximate center of the original image.
            :param: save (boolean): is set to True, the cropped image is saved to the data store and public_url is
            the url for the cropped image. False public_url is for the original image.
            :return: (None) stores the new image in self.cropped
        """
        redYpercent = .07
        redXpercent = .45

        blueYpercent = .09
        blueXpercent = .55

        greenYpercent = .15
        greenXpercent = .65

        # Determine cut size based on type of image
        # cut_size (portionX, portionY)
        if 'red' in self.image_id:
            text = 'red'
            cut_size = (self.pic.size[0]*redXpercent, self.pic.size[1]*redYpercent)
        elif 'blue' in self.image_id:
            text = 'blue'
            cut_size = (self.pic.size[0]*blueXpercent, self.pic.size[1]*blueYpercent)
        elif 'green' in self.image_id:
            text = 'green'
            cut_size = (self.pic.size[0]*greenXpercent, self.pic.size[1]*greenYpercent)
        else:
            text = 'production'
            cut_size = (self.pic.size[0]*blueXpercent, self.pic.size[1]*blueYpercent)

        config.logging.debug('Image Size ({1}) = {0}'.format(self.pic.size, text))

        # image_center (centerX, centerY)
        image_center = self.pic.size[0]/2, self.pic.size[1]/2

        # box (startX, startY, endX, endY)
        box = ((image_center[0]-int(cut_size[0]/2)), (image_center[1]-int(cut_size[1]/2)),
               (image_center[0]+int(cut_size[0]/2)), (image_center[1]+int(cut_size[1]/2)))
        self.cropped = self.pic.crop(box)

        if save:
            try:
                # Save temp file
                self.cropped.save('/home/Cesar/temp/{0}'.format(self.image_id))
                media_body = MediaFileUpload('/home/Cesar/temp/{0}'.format(self.image_id),
                                             mimetype='image/jpg')
                body = {
                    'name': self.image_id,
                    # 'predefinedAcl': 'publicRead'
                }
                request = self.storage_api.objects().insert(bucket=BUCKET_CROPPED,
                                                            predefinedAcl='publicRead',
                                                            body=body,
                                                            media_body=media_body)
                resp = request.execute()
                self.public_url_cropped = 'https://{0}.storage.googleapis.com/{1}'.format(config.BUCKET_CROPPED, self.image_id)
            except errors.HttpError, error:
                config.logging.error('HTTP error occurred: {0}'.format(error))
            else:
                config.logging.debug('Image [{0}] saved successfully to [{1}]'.format(resp['name'],
                                                                                      config.BUCKET_CROPPED))
                config.logging.debug('Cropped Image [{0}] size = {1}'.format(resp['name'], self.cropped.size))
        else:
            self.public_url_cropped = 'https://{0}.storage.googleapis.com/{1}'.format(config.BUCKET_CROPPED,
                                                                                      self.image_id)

    def get_public_url_original(self):
        """
        Gets the public_url of the image
            :return: public_url_original (string) if image saved to datastore, empty otherwise
        """
        return self.public_url_original

    def get_public_url_cropped(self):
        """
        Gets the public_url of the image
            :return: public_url_cropped (string) if image saved to datastore, empty otherwise
        """
        return self.public_url_cropped
