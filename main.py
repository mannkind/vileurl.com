import cgi 
import wsgiref.handlers
from random import sample
from random import choice
from random import randint
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext import db

"""
Word Lists

AlphaNumeric = A-Za-z0-9
VileWords = (look in dictionary.txt)

"""
def _alphanumeric():
  digits = [chr(i) for i in xrange(ord('0'), ord('9')+1)]
  lower = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
  upper = [chr(i) for i in xrange(ord('A'), ord('Z')+1)]
  a = list()
  a[-1:] = upper
  a[-1:] = lower
  a[-1:] = digits

  return a

def _vilewords():
  return [line.strip() for line in open('dictionary.txt')]

alphanumeric = _alphanumeric()
vilewords = _vilewords()

"""
Classes

UrlData - The datamodel... holds the url <=> hash association
Index - For viewing the index page and redirecting visitors
Create - For creating a new hash and displaying the result

"""
class UrlData(db.Model):
  url = db.StringProperty()
  hash = db.StringProperty()

class Index(webapp.RequestHandler):
  def get(self, param):
    if param:
      url = self._getUrl(param)
      self.redirect(url)
      return

    from os import path
    path = path.join(path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, { 
      'offensive': choice(vilewords),
      'results': False 
    }))

  def _getUrl(self, hash):
    data = UrlData.gql('WHERE hash = :1 LIMIT 1', hash)
    return data.fetch(1)[0].url if data.count(1) == 1 else '/'
    

class Create(webapp.RequestHandler):

  """
  Create is the page that the form is submitted to...

    * Determine if we should redirect to HolyURL
    * Determine if we have a URL to Violate
    * Violate the URL
    * Render page
  """
  def get(self):

    # If someone clicked the jesusplzkthx button, forward to holyurl.com
    jesusplz = self.request.get('jesusplzkthx')
    if jesusplz:
      self.redirect('http://www.holyurl.com', False)
      return

    # Determine if we have a URL to violate
    url = self.request.get('url')
    if not url:
      self.redirect('/', False)
      return

    # Parse the URL, add http:// if it doesn't exist
    from urlparse import urlparse
    if not urlparse(url).scheme:
      url = ''.join(['http://', url])

    # Violate the URL
    hash = self._getHash(url)

    # Setup the template variables for rendering the page
    template_vars = {
      'offensive': choice(vilewords),
      'results': True,
      'url': url,
      'hash': ''.join(['http://vileurl.com/', hash])
    }

    # Render the page to the user
    from os import path
    path = path.join(path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_vars))

  """
  Determine if the hash already exists in the datatable
  """
  def _hashExists(self, hash):
    return UrlData.gql('WHERE hash = :1 LIMIT 1', hash).count(1) == 1

  """
  Generate a new hash... doesn't remotely take the real URL into consideration
  """
  def _newHash(self, url):
    global alphanumeric, vilewords
    separators = ['-', '_', '.']

    parts = [
      choice(separators).join(sample(vilewords, randint(1,3))),
      choice(separators), 
      ''.join(sample(alphanumeric, randint(5, 7))),
      choice(separators),
      choice(separators).join(sample(vilewords, randint(1,3)))] 

    hash = ''.join(parts)
    while self._hashExists(hash):
      hash = _newHash(url)
    
    UrlData(url = url, hash = hash).put()
    return hash

  """
  Get the hash for the URL if it exists; create a hash for the URL if one doesn't exist
  """
  def _getHash(self, url):
    data = UrlData.gql('WHERE url = :1 LIMIT 1', url)
    return data.fetch(1)[0].hash if data.count(1) == 1 else self._newHash(url)

"""
It all starts here
"""
def main():
  application = webapp.WSGIApplication([('/create', Create), ('/(.*)', Index)], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
