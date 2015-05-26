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
        try:
            if queue:
                self.queue = queue
                self.task = self._get_next_task_from_queue()
                self.id = self.task['id']
                config.logging.debug('task (queue): Task ID: {0}'.format(self.id))
                self.payload = self.task['payloadBase64'].decode('base64')
                config.logging.debug('task (queue): Task Payload: {0}'.format(self.payload))
                p, image_name = self.id.split('--')
                config.logging.debug('task (queue): Task Image Name: {0}'.format(image_name))
                self.image = Picture('{0}.jpg'.format(image_name))
            elif task_id:
                self.queue = config.QUEUE
                self.task = self._get_task_from_queue(task_id, refresh_lease=True)
                self.id = self.task['id']
                config.logging.debug('task (queue): Task ID: {0}'.format(self.id))
                self.payload = self.task['payloadBase64'].decode('base64')
                config.logging.debug('task (queue): Task Payload: {0}'.format(self.payload))
                p, image_name = self.id.split('--')
                config.logging.debug('task (queue): Task Image Name: {0}'.format(image_name))
                self.image = Picture('{0}.jpg'.format(image_name))
                # TODO: Refresh the lease on the task!!
        except TypeError:
            raise TypeError

    def _get_next_task_from_queue(self):
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
                                                   leaseSecs=config.READING_LEASE_TIME,
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

    def _get_task_from_queue(self, task_id, refresh_lease):
        """
        Gets and leases the task associated with the task_id from the pull task queue.
            :param: task_id
                    refresh_lease: If true, refreshes the lease on the task
            :return: Leased Task.
        """
        try:
            http = httplib2.Http()
            c = credentials.get_credentials()
            if c:
                task_api = build('taskqueue', 'v1beta2', http=c.authorize(http))
                get_req = task_api.tasks().get(project='s~ocr-backend',
                                               taskqueue=self.queue,
                                               task=task_id)
                result = get_req.execute()
                if 'id' in result:
                    if refresh_lease:
                        self.refresh_lease_time()
                    return result
                else:
                    return None

            else:
                config.logging.error('Error getting credentials')
        except httplib2.ServerNotFoundError as e:
            config.logging.error('HTTP Error {0}'.format(e.message))
            return None

    def refresh_lease_time(self):
        """
        TODO: implement update Task API method
        """
        return True

    def move_to_queue(self, queue, payload, lease_time):
        """
        Modifies the payload of the tasks and moves it to a new queue. (ie. training or improve-cropping)
        """
        import time
        try:
            http = httplib2.Http()
            c = credentials.get_credentials()
            if c:
                task_api = build('taskqueue', 'v1beta2', http=c.authorize(http))
                body = {"kind": "taskqueues#task",
                        "id": self.id,
                        "queueName": queue,
                        "payloadBase64": str.encode(str(payload), encoding='base64'),
                        "enqueueTimestamp": long(time.time()),
                        "leaseTimestamp": lease_time,
                        "retry_count": 0}
                create_req = task_api.tasks().insert(project='s~ocr-backend',
                                                     taskqueue=queue,
                                                     body=body)
                result = create_req.execute()
                config.logging.info('task: insert - result: {0}'.format(result))
                if result:
                    self.delete_task_from_queue()
                    self.queue = queue
                    self.payload = payload
            else:
                config.logging.error('Error getting credentials')
        except httplib2.ServerNotFoundError as e:
            config.logging.error('HTTP Error {0}'.format(e.message))
            return None

    def delete_task_from_queue(self):
        """
        Deletes the task from the queue
        :return:
        """
        try:
            http = httplib2.Http()
            c = credentials.get_credentials()
            if c:
                task_api = build('taskqueue', 'v1beta2', http=c.authorize(http))
                delete_req = task_api.tasks().delete(project='s~ocr-backend',
                                                     taskqueue=self.queue,
                                                     task=self.id)
                result = delete_req.execute()
                config.logging.info('task: Delete task - result: {0}'.format(result))
            else:
                config.logging.error('Error getting credentials')
        except httplib2.ServerNotFoundError as e:
            config.logging.error('HTTP Error {0}'.format(e.message))
            return None
