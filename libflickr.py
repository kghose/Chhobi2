"""This module handles Flickr authentication and uploading of images to flickr.
The functions here do not do any storing of app key, app secret, oauth token, secret etc. The main GUI handles that.
The core code is lifted from https://github.com/michaelhelmick/python-flickr and adapted for our use. I started with
version 0.3.0
"""
import logging
logger = logging.getLogger(__name__)
import webbrowser, threading

import urllib, urllib2, mimetypes, mimetools, codecs, httplib2
from io import BytesIO
import oauth2 as oauth

try:
  from urlparse import parse_qsl
except ImportError:
  from cgi import parse_qsl

try:
  import simplejson as json
except ImportError:
  try:
    import json
  except ImportError:
    try:
      from django.utils import simplejson as json
    except ImportError:
      raise ImportError('A json library is required to use this python library.')

# We need to import a XML Parser because Flickr doesn't return JSON for photo uploads -_-
try:
  from lxml import etree
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
    except ImportError:
      try:
        #normal cElementTree install
        import cElementTree as etree
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
        except ImportError:
          raise ImportError('Failed to import ElementTree from any known place')

writer = codecs.lookup('utf-8')[3]

def get_content_type(filename):
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def iter_fields(fields):
  """Iterate over fields.

  Supports list of (k, v) tuples and dicts.
  """
  if isinstance(fields, dict):
    return ((k, v) for k, v in fields.iteritems())
  return ((k, v) for k, v in fields)


class FlickrAPIError(Exception):
  """ Generic catch-all error class"""
  def __init__(self, msg, error_code=None):
    self.msg = msg
    self.code = error_code
    if error_code is not None and error_code < 100:
      raise FlickrAuthError(msg, error_code)

  def __str__(self):
    return repr(self.msg)


class FlickrAuthError(FlickrAPIError):
  """ Raised when you try to access a protected resource and it fails due to some issue with your authentication. """
  def __init__(self, msg, error_code=None):
    self.msg = msg
    self.code = error_code

  def __str__(self):
    return repr(self.msg)


class FlickrAPI(object):
  def __init__(self, api_key=None, api_secret=None,
               oauth_token=None, oauth_token_secret=None,
               callback_url=None, headers=None, client_args=None):
    self.api_key = api_key
    self.api_secret = api_secret
    self.callback_url = callback_url

    self.oauth_token = oauth_token
    self.oauth_token_secret = oauth_token_secret

    self.api_base = 'http://api.flickr.com/services'
    self.rest_api_url = '%s/rest' % self.api_base
    self.upload_api_url = '%s/upload/' % self.api_base
    self.replace_api_url = '%s/replace/' % self.api_base
    self.request_token_url = 'http://www.flickr.com/services/oauth/request_token'
    self.access_token_url = 'http://www.flickr.com/services/oauth/access_token'
    self.authorize_url = 'http://www.flickr.com/services/oauth/authorize'

    self.headers = headers
    if self.headers is None:
      self.headers = {'User-agent': 'Python-Flickr v%s' % __version__}

    self.consumer = None
    self.token = None
    self.client_args = client_args or {}

    if not api_key or not api_secret:
      return

    self.set_state(oauth_token=oauth_token, oauth_token_secret=oauth_token_secret)

  def set_state(self, api_key=None, api_secret=None, oauth_token=None, oauth_token_secret=None):
    """Update auth internals as new information comes in."""
    if api_key is not None:
      self.api_key = api_key
      self.oauth_token = None
      self.oauth_token_secret = None
      self.token = None
    if api_secret is not None:
      self.api_secret = api_secret
      self.oauth_token = None
      self.oauth_token_secret = None
      self.token = None
    if oauth_token is not None: self.oauth_token = oauth_token
    if oauth_token_secret is not None: self.oauth_token_secret = oauth_token_secret

    if self.api_key is not None and self.api_secret is not None:
      self.consumer = oauth.Consumer(self.api_key, self.api_secret)

    if self.oauth_token is not None and self.oauth_token_secret is not None:
      self.token = oauth.Token(self.oauth_token, self.oauth_token_secret)

    # Filter down through the possibilities here - if they have a token, if they're first stage, etc.
    if self.consumer is not None and self.token is not None:
      self.client = oauth.Client(self.consumer, self.token, **self.client_args)
    elif self.consumer is not None:
      self.client = oauth.Client(self.consumer, **self.client_args)
    else:
      # If they don't do authentication, but still want to request unprotected resources, we need an opener.
      self.client = httplib2.Http(**self.client_args)

  def get_authentication_tokens(self, perms=None):
    """ Returns an authorization url to give to your user.

        Parameters:
        perms - If None, this is ignored and uses your applications default perms. If set, will overwrite applications perms; acceptable perms (read, write, delete)
                    * read - permission to read private information
                    * write - permission to add, edit and delete photo metadata (includes 'read')
                    * delete - permission to delete photos (includes 'write' and 'read')
    """

    request_args = {}
    resp, content = self.client.request('%s?oauth_callback=%s' % (self.request_token_url, self.callback_url), 'GET', **request_args)

    if resp['status'] != '200':
      raise FlickrAuthError('There was a problem retrieving an authentication url.')

    request_tokens = dict(parse_qsl(content))

    auth_url_params = {
      'oauth_token': request_tokens['oauth_token']
    }

    accepted_perms = ('read', 'write', 'delete')
    if perms and perms in accepted_perms:
      auth_url_params['perms'] = perms

    request_tokens['auth_url'] = '%s?%s' % (self.authorize_url, urllib.urlencode(auth_url_params))
    return request_tokens

  def get_auth_tokens(self, oauth_verifier):
    """ Returns 'final' tokens to store and used to make authorized calls to Flickr.

        Parameters:
            oauth_token - oauth_token returned from when the user is redirected after hitting the get_auth_url() function
            verifier - oauth_verifier returned from when the user is redirected after hitting the get_auth_url() function
    """

    params = {
      'oauth_verifier': oauth_verifier,
      }

    resp, content = self.client.request('%s?%s' % (self.access_token_url, urllib.urlencode(params)), 'GET')
    if resp['status'] != '200':
      raise FlickrAuthError('Getting access tokens failed: %s Response Status' % resp['status'])

    return dict(parse_qsl(content))

  def api_request(self, endpoint=None, method='GET', params={}, files=None, replace=False):
    self.headers.update({'Content-Type': 'application/json'})

    if endpoint is None and files is None:
      raise FlickrAPIError('Please supply an API endpoint to hit.')

    qs = {
      'format': 'json',
      'nojsoncallback': 1,
      'method': endpoint,
      'api_key': self.api_key
    }

    if method == 'POST':

      if files is not None:
        # To upload/replace file, we need to create a fake request
        # to sign parameters that are not multipart before we add
        # the multipart file to the parameters...
        # OAuth is not meant to sign multipart post data
        http_url = self.replace_api_url if replace else self.upload_api_url
        faux_req = oauth.Request.from_consumer_and_token(self.consumer,
                                                         token=self.token,
                                                         http_method="POST",
                                                         http_url=http_url,
                                                         parameters=params)

        faux_req.sign_request(oauth.SignatureMethod_HMAC_SHA1(),
                              self.consumer,
                              self.token)

        all_upload_params = dict(parse_qsl(faux_req.to_postdata()))

        # For Tumblr, all media (photos, videos)
        # are sent with the 'data' parameter
        all_upload_params['photo'] = (files.name, files.read())
        body, content_type = self.encode_multipart_formdata(all_upload_params)

        self.headers.update({
          'Content-Type': content_type,
          'Content-Length': str(len(body))
        })

        req = urllib2.Request(http_url, body, self.headers)
        try:
          req = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
          # Making a fake resp var because urllib2.urlopen doesn't
          # return a tuple like OAuth2 client.request does
          resp = {'status': e.code}
          content = e.read()

        # After requests is finished, delete Content Length & Type so
        # requests after don't use same Length and take (i.e 20 sec)
        del self.headers['Content-Type']
        del self.headers['Content-Length']

        # If no error, assume response was 200
        resp = {'status': 200}

        content = req.read()
        content = etree.XML(content)

        stat = content.get('stat') or 'ok'

        if stat == 'fail':
          if content.find('.//err') is not None:
            code = content.findall('.//err[@code]')
            msg = content.findall('.//err[@msg]')

            if len(code) > 0:
              if len(msg) == 0:
                msg = 'An error occurred making your Flickr API request.'
              else:
                msg = msg[0].get('msg')

              code = int(code[0].get('code'))

              content = {
                'stat': 'fail',
                'code': code,
                'message': msg
              }
        else:
          photoid = content.find('.//photoid')
          if photoid is not None:
            photoid = photoid.text

          content = {
            'stat': 'ok',
            'photoid': photoid
          }

      else:
        url = self.rest_api_url + '?' + urllib.urlencode(qs)
        resp, content = self.client.request(url, 'POST', urllib.urlencode(params), headers=self.headers)
    else:
      params.update(qs)
      resp, content = self.client.request('%s?%s' % (self.rest_api_url, urllib.urlencode(params)), 'GET', headers=self.headers)

    #try except for if content is able to be decoded
    try:
      if type(content) != dict:
        content = json.loads(content)
    except ValueError:
      raise FlickrAPIError('Content is not valid JSON, unable to be decoded.')

    status = int(resp['status'])
    if status < 200 or status >= 300:
      raise FlickrAPIError('Flickr returned a Non-200 response.', error_code=status)

    if content.get('stat') and content['stat'] == 'fail':
      raise FlickrAPIError('Flickr returned error code: %d. Message: %s' % \
                           (content['code'], content['message']),
                           error_code=content['code'])

    return dict(content)

  def get(self, endpoint=None, params=None):
    params = params or {}
    return self.api_request(endpoint, method='GET', params=params)

  def post(self, endpoint=None, params=None, files=None, replace=False):
    params = params or {}
    return self.api_request(endpoint, method='POST', params=params, files=files, replace=replace)

  # Thanks urllib3 <3
  def encode_multipart_formdata(self, fields, boundary=None):
    """
    Encode a dictionary of ``fields`` using the multipart/form-data mime format.

    :param fields:
        Dictionary of fields or list of (key, value) field tuples.  The key is
        treated as the field name, and the value as the body of the form-data
        bytes. If the value is a tuple of two elements, then the first element
        is treated as the filename of the form-data section.

        Field names and filenames must be unicode.

    :param boundary:
        If not specified, then a random boundary will be generated using
        :func:`mimetools.choose_boundary`.
    """
    body = BytesIO()
    if boundary is None:
      boundary = mimetools.choose_boundary()

    for fieldname, value in iter_fields(fields):
      body.write('--%s\r\n' % (boundary))

      if isinstance(value, tuple):
        filename, data = value
        writer(body).write('Content-Disposition: form-data; name="%s"; '
                           'filename="%s"\r\n' % (fieldname, filename))
        body.write('Content-Type: %s\r\n\r\n' %
                   (get_content_type(filename)))
      else:
        data = value
        writer(body).write('Content-Disposition: form-data; name="%s"\r\n'
                           % (fieldname))
        body.write(b'Content-Type: text/plain\r\n\r\n')

      if isinstance(data, int):
        data = str(data)  # Backwards compatibility

      if isinstance(data, unicode):
        writer(body).write(data)
      else:
        body.write(data)

      body.write(b'\r\n')

    body.write('--%s--\r\n' % (boundary))

    content_type = 'multipart/form-data; boundary=%s' % boundary

    return body.getvalue(), content_type

class Fup(FlickrAPI):
  """We make this a class so we can use a single FlickrAPI instance."""
  def setup_authorization(self, new=1):
    """Call this when you want a user to grant access to this application.
    Opens webbrowser to authentication page and returns oauth tokens

    callback_url='oob' indicates desktop application, and will cause flickr to return a numeric code
    1 http://www.mathworks.com/matlabcentral/fileexchange/34162-flickr-api-with-oauth-based-user-authentication/content/html/testFlickrApi.html
    2 http://www.flickr.com/groups/api/discuss/72157630326883668/
    """
    self.callback_url='oob'
    auth_props = self.get_authentication_tokens(perms='write')
    auth_url = auth_props['auth_url']
    webbrowser.open(auth_url, new=new)
    logger.debug(auth_props)
    self.set_state(oauth_token=auth_props['oauth_token'],oauth_token_secret=auth_props['oauth_token_secret'])

  def authorize(self, oauth_verifier=None):
    """Use the code the user types in to generate the credentials we need to login."""
    print self.oauth_token, self.oauth_token_secret
    final_tokens = self.get_auth_tokens(oauth_verifier)
    logger.debug(final_tokens)
    self.set_state(oauth_token=final_tokens['oauth_token'], oauth_token_secret=final_tokens['oauth_token_secret'])

  def upload_files(self, fnames, callback_func=None):
    """Pass in a list of file names for upload. If you pass a callback_func, it will be called as
    callback_func(msg) with a message every time a file has been uploaded."""
    callback_func('Preparing to upload {:d} files'.format(len(fnames)))
    upload_thread = threading.Thread(target=self.threaded_upload, name='Thread', args=(fnames,callback_func))
    upload_thread.start()

  def threaded_upload(self, fnames, callback_func=None):
    cnt=0
    for f in fnames:
      logger.debug('Uploading {:s}'.format(f))
      self.post(files=open(f,'rb')) #Returns photo id. Need file object
      if callback_func: callback_func('Uploaded {:s}'.format(f))
      cnt += 1
    if callback_func: callback_func('Finished uploading {:d} photos'.format(cnt))

if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  f = Fup(api_key='d2e06f914a97cc50a1d8532abe7fccac', api_secret='d0d8d059521cbc2b', headers={'User-agent': 'Chhobi'})
  f.setup_authorization()
  verifier = raw_input('Verification code: ')
  f.authorize(verifier)
  recent_activity = f.get('flickr.activity.userComments')
  print recent_activity