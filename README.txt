PyCODA
======

Pycoda is a thin wrapper on the CODA API.

For documentation of the API itself, see http://support.camvine.com/kb/api/

How to use
----------

An application needs to authenticate itself with CODA using the OAuth standard -
this involves two parts:

* First, it needs to be using a valid Consumer Key and Secret which 
  identifies the app.

* Second, it needs an Access Token which represents its authority to 
  act on behalf of a particular user in a particular organisation.

Because of this, the most complex bits happen at the beginning and are to do with
authentication. This is a pity, but we'll show you the steps, and once you've got
through this, the rest is easy!

Let's get started. You can try this stuff out at the Python prompt, if wanted: just
start up Python in the directory which contains pycoda as a subdirectory.

First, you'll need a Consumer Key and Secret for your particular application.  (Your application will be a 'consumer' of the API - hence the name.)
You can create these by going to:

  https://www.codaview.com/gui/developer/

adding a new application, and it'll then have an associated 'OAuth Key' and 'OAuth Secret'. You can copy these and hard-code them into your app.

Your app can then identify itself to the Coda server:

   CONSUMER_KEY = 'XXXXXXXXXXXXXX'
   CONSUMER_SECRET = 'YYYYYYYYYYYYYY'
   from pycoda.api import CodaServer
   s = CodaServer(CONSUMER_KEY, CONSUMER_SECRET)

Now, when a particular user runs your application, it will need an 'access token', 
which represents the app's authority to connect to CODA and pretend to be that user.

If you don't have an access token for the user, you need to do this:

   (rtok, url) = s.get_auth()

Then the user should go to the resulting url and grant access to their account,  
just as they would with a Flickr, Facebook or Twitter app. 

Once the user has visited the url and approved the request, you can get the
access token:

   atok = s.get_access_token(rtok)

atok will look something like this:

  "oauth_token_secret=8rGSdemBs2zne2yV&oauth_token=8a8u79TUnbWKs3Bp"

and you should store it somewhere - in a file, in a database, wherever is
appropriate for the particular app. The user won't then have to go and authorise on
the website next time around.


OK - that's the complicated stuff.  It wasn't too hard, was it? 
The rest is even easier.

Get a Coda object from the server:

   c = s.get_coda(atok)

Ask it for a list of displays in my organisation:

   print c.getDisplays()

Get a list of content sources that have the word 'NASA' in their name:

   srcs = c.getSources(name='NASA')

And print the first one.

   print srcs[0]

Almost all objects in CODA have a unique identifier or 'UUID', which looks
something like this: 3c554dfe-f094-5f7e-0010-000000006c43

That's what you use to refer to the item, be it a source or display, in other
calls. You'll see parameters called source_uuid, display_uuid etc.

Let's get the UUID of this source:

   print srcs[0]['source_uuid']

If you want to put a particular source on a particular display, you say:

   c.assignSource(source_uuid=su, display_uuids=[ du ])

where su and du are the source_uuid and display_uuid required. Note that the
display_uuids parameter is a list, because you can specify more than one if you
want to assign the same source to multiple displays simultaneously.

Note that, unlike normal Python calls, if you're passing arguments to calls
you *must* use keyword arguments because the keywords get turned automatically 
into the parameter names.   In other words:

   c.removeUser(user_uuid='xxxxxxxxx')

will work but

   c.removeUser('xxxxxxxxx')

will not, even though the call only takes one parameter.

That should give you enough to get started!  Go to: 
    
    http://support.camvine.com/kb/api/

to see the other calls you can make.

Testing
-------

The codatests.py file has some simple unit tests.  It needs an authentication token, which it will read from a file called codatests.tok, if such a file exists in the current directory, otherwise it will open up a browser, prompt you to confirm on the CODA site that the app should be granted access to your account, and will then create the codatests.tok file for you.

The token file should simply contain an auth token in JSON string format: typically a single line looking something like:

"oauth_token_secret=h2Je4chGHwXXYXaD8&oauth_token=LZUaj3UuwB8u9TYH"

Acknowledgements
----------------

The oauth.py file, by Leah Culver, is from the Google Code project at
 http://code.google.com/p/oauth/


                            Quentin Stafford-Fraser
                            quentin@camvine.com

