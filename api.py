#! /usr/bin/python
#
# A front end to the CODA API.
# For more information, see http://support.camvine.com/kb/api/
#
# Copyright 2010 Cambridge Visual Networks Ltd - Quentin Stafford-Fraser

# Example use:
#    CONSUMER_KEY = '50d83d409d7745d0'
#    CONSUMER_SECRET = '564a288948ba25b0'
#    from pycoda.api import CodaServer
#    s = CodaServer(CONSUMER_KEY, CONSUMER_SECRET)
#
# If you don't have an access token, do this:
#    (rtok, url) = s.get_auth()
# When user has visited url and approved the request, you can get the access token:
#    atok = s.get_access_token(rtok)
# which can be stored somewhere.
#
# An access token atok will look something like: 
#    "oauth_token_secret=8rGSdemBs2zne2yV&oauth_token=8a8u79TUnbWKs3Bp" 
#
# Then get a Coda object from the server:
#    c = s.get_coda(atok)
#    print c.getDisplays()
#

CODA_SERVER_URL = 'https://api.codaview.com' # Note no trailing slashe
API_RELATIVE_URL = "external/v2/json/"  # Note trailing slash

import os
import oauth
import urllib2
import sys

# Find a simplejson library somewhere!
try:
    import json  # Python 2.6 onwards
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        "Please install the simplejson module or update to a Python version which includes json"

class CodaServer(object):
    def __init__(self, consumer_key, consumer_secret, server_url = CODA_SERVER_URL):
        self.server_url = server_url
        self.consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
    
    def get_auth(self):
        """
        Return an auth token and a URL that the user needs to visit to authorise the request
        """
        # Get an initial request token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer,
            http_url='%s/oauth/request_token/' % self.server_url,
            parameters={})
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, None)
        response = urllib2.urlopen(oauth_request.to_url())
        request_token_string = response.read()
        request_token = oauth.OAuthToken.from_string(request_token_string)

        # Authentication request
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer,
            token=request_token,
            http_url='%s/oauth/authorize/' % self.server_url,
            parameters={})
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, request_token)

        return (request_token_string, oauth_request.to_url())
    
    def get_access_token(self, request_token_string):
        # Note this uses and returns the string form of the tokens
        request_token = oauth.OAuthToken.from_string(request_token_string)
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   token=request_token,
                                                                   http_url='%s/oauth/access_token/' % self.server_url,
                                                                   parameters={})
        
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, request_token)
        response = urllib2.urlopen(oauth_request.to_url())
        access_token_string=response.read()
        return access_token_string
            
    def get_coda(self, access_token):
        # Note this takes the string form of the access token
        return Coda(access_token, "%s/%s" % (self.server_url,API_RELATIVE_URL), self.consumer)
        

class CodaException(Exception):
    def __init__(self, message):
        self.msg = message
    def __str__(self):
        return repr(self.msg)
        
class DictObj(dict):
    """ A dict that also supports d.key syntax as an alias for d['key'] """
    def __getattr__(self, name):
        return self[name]

class Coda(object):
    def __init__(self, access_token_string, api_url, consumer):
        self.api_url = api_url
        self.consumer = consumer
        self.access_token = oauth.OAuthToken.from_string(access_token_string)

    def get_url(self, method, parameters={}):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   token=self.access_token,
                                                                   http_url=self.api_url + method,
                                                                   parameters=parameters)
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, self.access_token)
        return oauth_request.to_url()
    
    def callMethod(self, method, **args):
        if not method.endswith('/'):
            method += '/'
        response = urllib2.urlopen(self.get_url(method, args))
        result = json.loads(response.read())
        if result['result'] == 'OK':
            return result.get('response', None)
        else:
            raise CodaException(result['error'])
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: self.callMethod(name, *args, **kwargs)
                    