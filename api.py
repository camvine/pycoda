#! /usr/bin/python
#
# A simple front end to the CODA API.
# For more information about the API, see http://support.camvine.com/kb/api/
#
# Copyright 2011 Cambridge Visual Networks Ltd - Quentin Stafford-Fraser
#
# How to use
# ==========
#
# The most complex bits happen at the beginning and are to do with authentication.
# This is a pity, but once you've done this, the rest is easy.
#
# You'll need a Consumer Key and Secret for your particular application.
# You can create these by going to:
#
#   https://www.codaview.com/gui/developer/
#
# and hard-code them into your app.
#
# Your app can then identify itself to the Coda server:
#
#    CONSUMER_KEY = 'XXXXXXXXXXXXXX'
#    CONSUMER_SECRET = 'YYYYYYYYYYYYYY'
#    from pycoda.api import CodaServer
#    s = CodaServer(CONSUMER_KEY, CONSUMER_SECRET)
#
# Now, when a particular user runs your application, it will need an 'access token', 
# which represents the app's authority to connect to CODA and pretend to be that user.
#
# If you don't have an access token for the user, you need to do this:
#
#    (rtok, url) = s.get_auth()
#
# The user should go to the resulting and grant access to their account,  
# just as they would with a Flickr, Facebook or Twitter app. 
#
# Once the user has visited url and approved the request, you can get the
# access token:
#
#    atok = s.get_access_token(rtok)
#
# which can be stored somewhere - in a file, in a database, whatever is appropriate
# for the particular app.
#
# An access token atok will look something like: 
#    "oauth_token_secret=8rGSdemBs2zne2yV&oauth_token=8a8u79TUnbWKs3Bp" 
#
# OK - that's the complicated stuff.  The rest is easy.
#
# Get a Coda object from the server:
#
#    c = s.get_coda(atok)
#
# Ask it for a list of displays in my organisation:
#
#    print c.getDisplays()
#
# Get a list of content sources that have the word 'NASA' in their name:
# 
#    srcs = c.getSources(name='NASA')
#
# And print the first one.
#
#    print srcs[0]
#
# Almost all objects in CODA have a unique identifier or 'UUID', which looks something
# like this: 3c554dfe-f094-5f7e-0010-000000006c43
# That's what you use to refer to the item, be it a source or display, in other calls.  
# Let's get the UUID of this source:
#
#    print srcs[0]['source_uuid']
#
# If you want to put a particular source on a particular display, you say:
#
#    c.assignSource(source_uuid=su, display_uuids=[ du ])
#
# where su and du are the source_uuid and display_uuid required.
# Note that the display_uuids parameter is a list, because you can assign
# the same source to multiple displays simultaneously.
#
# Note that, unlike normal Python calls, if you're passing arguments to calls
# you *must* use keyword arguments because the keywords get turned automatically 
# into the parameter names.   In other words:
#    c.removeUser(user_uuid='xxxxxxxxx')
# will work but
#    c.removeUser('xxxxxxxxx')
# will not, even though the call only takes one parameter.
#
# That should give you enough to get started!

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
                    