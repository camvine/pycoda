#! /usr/bin/env python

# =================================
# = Simple unit tests for pycoda =
# =================================
#
# These will store/use an authentication token in codatests.tok in the current directory.
# This is just a simple test - a very long way from being exhaustive!
#  
# Some tests may fail if the organisation's account is in active use, and data on server is changing 
# while these tests are being performed.  Should be otherwise harmless, though.

import unittest
import api
import os, sys, webbrowser, urllib2, time
import random

TEST_KEY = 'c1361963e1c2475f'
TEST_SECRET = '2cec36b84c7811c2'
TOKEN_FILENAME = 'codatests.tok'

HTTPError = urllib2.HTTPError

# Find a simplejson library somewhere!
try:
    import json  # Python 2.6 onwards
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        "Please install the simplejson module or update to a Python version which includes json"

class AuthTestCase(unittest.TestCase):
    
    def setUp(self):
        self.codaserver = api.CodaServer(TEST_KEY,TEST_SECRET)
        self.atok = None
        if os.path.isfile(TOKEN_FILENAME):
            tf = open(TOKEN_FILENAME, 'r')
            print "\nLoading auth token from %s" % TOKEN_FILENAME
            self.atok = json.load(tf)
            tf.close()
        if not self.atok:
            (rtok, url) = self.codaserver.get_auth()
            print "Opening web browser to confirm authentication request\nat %s\nPlease approve and then press return here" % url
            import webbrowser
            webbrowser.open(url)
            sys.stdin.readline()
            self.atok = self.codaserver.get_access_token(rtok)
            tf = open(TOKEN_FILENAME, 'w')
            print "Saving auth token to %s" % TOKEN_FILENAME
            json.dump(self.atok, tf)
            tf.close()

        self.coda = self.codaserver.get_coda(self.atok)
            
    def testAuth(self):
        # Check an invalid auth
        self.assertRaises(api.CodaException, lambda: self.codaserver.get_access_token("oauth_token_secret=randomstring&oauth_token=anotherstring"))

    def testGetUser(self):
        resp = self.coda.getUser()
        self.assertTrue(resp.has_key('user_uuid'))
        self.assertTrue(resp.has_key('username'))

    def testGetOrganisation(self):
        resp = self.coda.getOrganisation()
        self.assertTrue(resp.has_key('name'))
        self.assertTrue(resp.has_key('organisation_uuid'))
        
    def testUsers(self):
        """List users, create and delete a user"""
        orig_users = self.coda.getUsers()
        new_user_name = 'test_user_' + str(int(time.time()))
        resp = self.coda.createUser(username=new_user_name, 
            first_name="Test", last_name="User", email="test@example.com", 
            password="wibble"+str(int(time.time())), permission=3)
        new_user_uuid = resp['user_uuid']
        resp = self.coda.getUsers(user_uuid=new_user_uuid)
        new_users = self.coda.getUsers()
        self.assertEqual(len(new_users), len(orig_users)+1, "Count of users didn't change after adding one")
        self.coda.removeUser(user_uuid=new_user_uuid)
        new_users = self.coda.getUsers()
        self.assertEqual(len(new_users), len(orig_users))

    def testDisplays(self):
        """List display, and try a simple modification on one"""
        displays = self.coda.getDisplays()
        # Pick a display at random
        disp = random.choice(displays)
        uuid = disp['display_uuid']
        
        # Add a new tag - not the most exciting test, I know, but we're using live displays here
        tags = disp['tags']
        num_tags = len(tags)
        new_tag = "test_tag_%d" % random.randint(0, 314156)
        self.coda.modifyDisplay(display_uuid = uuid, tags=tags+[new_tag])
        
        # Read the info again and check it's there
        new_disp_info = self.coda.getDisplays(display_uuid = uuid)
        new_tags = new_disp_info[0]['tags']
        self.assertEqual(len(new_tags), num_tags+1)
        self.assertTrue(new_tag in new_tags)
        
        # Remove it and check it's gone.
        new_tags.remove(new_tag)
        self.coda.modifyDisplay(display_uuid = uuid, tags=new_tags)
        final_disp_info = self.coda.getDisplays(display_uuid = uuid)
        final_tags = new_disp_info[0]['tags']
        self.assertEqual(len(final_tags), num_tags)
        self.assertTrue(new_tag not in new_tags)
    

        
    def testSources(self):
        """List sources, create and delete a source"""
        orig_sources = self.coda.getSources()
        new_source_name = 'test_src_' + str(int(time.time()))
        resp = self.coda.createSource(name=new_source_name, 
            type_uuid = '3c554dfe-f094-5f7e-0013-000000000010', # an HTML page
            parameters = json.dumps({'url':"http://news.google.com"}))
        new_source_uuid = resp['source_uuid']
        # Check we can read both that single UUID...
        resp = self.coda.getSources(source_uuid=new_source_uuid)
        self.assertEqual(new_source_uuid, resp[0]['source_uuid'])
        # and a list containing just that uuid
        resp = self.coda.getSources(source_uuids=[new_source_uuid])
        self.assertEqual(len(resp), 1)
        self.assertEqual(new_source_uuid, resp[0]['source_uuid'])

        new_sources = self.coda.getSources()
        self.assertEqual(len(new_sources), len(orig_sources)+1, "Count of sources didn't change after adding one")
        # Search for sources with this name
        srch_src = self.coda.getSources(name=new_source_name)
        # Check there's only one and it has the right uuid
        self.assertEqual(len(srch_src), 1)
        self.assertEqual(new_source_uuid, srch_src[0]['source_uuid'])
        
        # Search for multiple sources (just one for now!)
        # XXX This may not be live on the server yet!
        #
        srch_src = self.coda.getSources(source_uuids=[new_source_uuid])
        # Check there's only one and it has the right uuid
        self.assertEqual(len(srch_src), 1)
        self.assertEqual(new_source_uuid, srch_src[0]['source_uuid'])
        
        # The delete it and check it's gone
        self.coda.removeSource(source_uuid=new_source_uuid)
        new_sources = self.coda.getSources()
        self.assertEqual(len(new_sources), len(orig_sources))
        srch_src = self.coda.getSources(name=new_source_name)
        self.assertEqual(len(srch_src), 0)
        

if __name__ == '__main__':
    unittest.main()
    