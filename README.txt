PyCODA
------

Pycoda is a thin wrapper on the CODA API.
See the comments at the top of api.py for examples of use.
For documentation of the API itself, see http://support.camvine.com/kb/api/

The Coda object constructs URLs on the fly, so if other methods are added at the CODA server, you should be able to call them without updating this library, assuming they follow the same pattern of URL, arguments and responses.

Testing
-------

The codatests.py file has some simple unit tests.  It needs an authentication token, which it will read from a file called codatests.tok, if such a file exists in the current directory, otherwise it will open up a browser, prompt you to confirm on the CODA site that the app should be granted access to your account, and will then create the codatests.tok file for you.

The file should simply contain an auth token in JSON string format: typically a single line looking something like:

"oauth_token_secret=h2Je4chGHwXXYXaD8&oauth_token=LZUaj3UuwB8u9TYH"


                            Quentin Stafford-Fraser
                            quentin@camvine.com
