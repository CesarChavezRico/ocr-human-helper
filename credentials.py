"""
Class that handles all the requirements for authentication within the same GC project
"""
__author__ = 'Cesar'

import config
import requests
from oauth2client import client as oauth2_client


def get_credentials():
    """
    Gets the credentials needed to perform the authentication within the same project
        :return: credentials
    """
    metadata_server = 'http://metadata/computeMetadata/v1/instance/service-accounts'
    service_account = 'default'
    token_uri = '{0}/{1}/token'.format(metadata_server, service_account)
    headers = {'Metadata-Flavor': 'Google'}
    r = requests.get(token_uri, headers=headers)
    if r.status_code == 200:
        d = r.json()
        return oauth2_client.AccessTokenCredentials(d['access_token'], 'my-user-agent/1.0')
    else:
        config.logging.error('Error in response from server: {0}'.format(r.status_code))
        config.logging.error('Error in response from server content: {0}'.format(r.content))
        return False
