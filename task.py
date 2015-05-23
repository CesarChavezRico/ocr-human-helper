__author__ = 'Cesar'

import config
import credentials
import httplib2
from picture import Picture
from apiclient.discovery import build


class Task:

    queue = None
    task = None
    id = None
    payload = None
    image = None

    def __init__(self, queue=None, task_id=None):
        """
        task constructor
        :param: queue to get any task from the queue. task_id to get a specific task already leased
        :return:
        """
        if queue:
            self.queue = queue
            self.task = self._get_task_from_queue()
            self.id = self.task['id']
            config.logging.debug('task (queue): Task ID: {0}'.format(self.id))
            self.payload = self.task['payloadBase64'].decode('base64')
            config.logging.debug('task (queue): Task Payload: {0}'.format(self.payload))
            p, image_name = self.id.split('--')
            config.logging.debug('task (queue): Task Image Name: {0}'.format(image_name))
            self.image = Picture('{0}.jpg'.format(image_name))
        elif task_id:
            # TODO: Refresh the lease on the task!!
            self.id = task_id
            p, image_name = self.id.split('--')
            self.image = Picture('{0}.jpg'.format(image_name))
            config.logging.debug('task (task_id): Task Image Name: {0}'.format(image_name))

    def _get_task_from_queue(self):
        """
        Gets and leases one available tasks from the pull task queue.
            :return: Leased Task.
        """
        try:
            http = httplib2.Http()
            c = credentials.get_credentials()
            if c:
                task_api = build('taskqueue', 'v1beta2', http=c.authorize(http))
                lease_req = task_api.tasks().lease(project='ocr-backend',
                                                   taskqueue=self.queue,
                                                   leaseSecs=60,
                                                   numTasks=1)
                result = lease_req.execute()
                if 'items' in result:
                    if result['items'] is not None:
                        task = result['items'][0]
                        return task
                    else:
                        return None
                else:
                    return None

            else:
                config.logging.error('Error getting credentials')
        except httplib2.ServerNotFoundError as e:
            config.logging.error('HTTP Error {0}'.format(e.message))
            return None
