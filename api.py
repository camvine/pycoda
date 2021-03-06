#! /usr/bin/python
#
# A simple front end to the CODA API.
# For more information about the API, see http://support.camvine.com/kb/api/
# For examples on how to use this, see README.txt.
#
# Copyright 2011 Cambridge Visual Networks Ltd - Quentin Stafford-Fraser
# 
# This code is released under the GNU General Public License v2.
# See COPYRIGHT.txt and LICENSE.txt.

CODA_SERVER_URL = 'https://api.codaview.com' # Note no trailing slashe
API_RELATIVE_URL = "external/v2/json/"  # Note trailing slash

import os
import oauth
import urllib, urllib2
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
    
    def get_auth(self, callback=None):
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
        params = {}
        if callback: params['oauth_callback']=callback
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer,
            token=request_token,
            http_url='%s/oauth/authorize/' % self.server_url,
            parameters=params)
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
        try:
            response = urllib2.urlopen(oauth_request.to_url())
            access_token_string=response.read()
        except urllib2.HTTPError, e:
            # print "CODA server said %s: %s" % (e.code, e.msg)
            raise CodaException("CODA server said %s: %s" % (e.code, e.msg))
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

    def get_url_and_postdata(self, method, parameters={}):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   token=self.access_token,
                                                                   http_method='POST',
                                                                   http_url=self.api_url + method,
                                                                   parameters=parameters)
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, self.access_token)
        return oauth_request.get_normalized_http_url(), oauth_request.to_postdata()
    
    def callMethod(self, method, **kwargs):
        if not method.endswith('/'):
            method += '/'
        params = {}
        # print "Calling %s with kwargs %s" % (method, kwargs)
        # API Marshalling guide just says that dicts and lists should be in JSON format
        for k in kwargs:
            v = kwargs[k]
            if isinstance(v, dict) or isinstance(v, list):
                params[k] = json.dumps(v)
            else:
                params[k] = v
        url, postdata = self.get_url_and_postdata(method, params)
        response = urllib2.urlopen(url, postdata)
        data = response.read()
        result = json.loads(data)
        if result['result'] == 'OK':
            return result.get('response', None)
        else:
            raise CodaException(result['error'])
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: self.callMethod(name, *args, **kwargs)
                    