__author__ = 'Cesar'

from apiclient.discovery import build
import config


def post_result_to_app_engine(result, task_name, task_payload):
    """
    Notifies the main app in app engine by calling its API. app engine is responsible of deleting the task from
    the task queue after successfully updating the reading entity on the datastore
        :return: True if success, Exception otherwise
    """
    api_root = 'https://ocr-backend.appspot.com/_ah/api'
    api = 'backend'
    version = 'v1'
    discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (api_root, api, version)

    backend = build(api, version, discoveryServiceUrl=discovery_url)
    payload = {"error": "",
               "result": result,
               "task_name": task_name,
               "task_payload": task_payload,
               "human": True
               }

    request = backend.reading().set_image_processing_result(body=payload)
    response = request.execute()

    if response['ok']:
        return True
    else:
        config.logging.error('Bad Response from AppEngine: {0}'.format(response))
        raise Exception


def notify_error_to_app_engine(error, task_name, task_payload):
    """
    Notifies the main app in app engine that there's an error by calling its API. app engine is responsible
    of deleting the task from the task queue after successfully notifying the user that the image sent could not
    be processed.
        :return: True if success, Exception otherwise
    """
    api_root = 'https://ocr-backend.appspot.com/_ah/api'
    api = 'backend'
    version = 'v1'
    discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (api_root, api, version)
    backend = build(api, version, discoveryServiceUrl=discovery_url)
    payload = {"error": error,
               "result": 0,
               "task_name": task_name,
               "task_payload": task_payload,
               "human": True
               }
    request = backend.reading().set_image_processing_result(body=payload)
    response = request.execute()
    if response['ok']:
        return True
    else:
        config.logging.error('Bad Response from AppEngine: {0}'.format(response))
        raise Exception
