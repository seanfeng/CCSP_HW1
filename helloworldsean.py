from django.utils import simplejson
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import run_wsgi_app

import os


class Greeting(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)


class MainPage(webapp.RequestHandler):
    def get(self):
        userAgent = self.request.headers['User-Agent']
        if -1 != userAgent.find('Chrome'):
            browser = 'Chrome'
        elif -1 != userAgent.find('Firefox'):
            browser = 'Firefox'
        elif -1 != userAgent.find('MSIE'):
            browser = 'MSIE'
        elif -1 != userAgent.find('Safari'):
            browser = 'Safari'

        greetings = db.GqlQuery("SELECT * FROM Greeting ORDER BY date DESC LIMIT 10")

        if users.get_current_user():
            username = users.get_current_user()
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            username = ''
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {'browser' : browser,
                           'greetings' : greetings,
                           'username' : username,
                           'url' : url,
                           'url_linktext' : url_linktext}

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))


class RPCHandler(webapp.RequestHandler):
    """ Allows the functions defined in the RPCMethods class to be RPCed."""
    def __init__(self):
        webapp.RequestHandler.__init__(self)
        self.methods = RPCMethods()

    def post(self):
        args = simplejson.loads(self.request.body)
        func, args = args[0], args[1:]

        if func[0] == '_':
            self.error(403) # access denied
            return

        func = getattr(self.methods, func, None)
        if not func:
            self.error(404) # file not found
            return

        result = func(*args)
        self.response.out.write(simplejson.dumps(result))


class RPCMethods:
    def Add(self, *args):
        greeting = Greeting()
        greeting.author = users.get_current_user()
        greeting.content = args[0]
        return [str(greeting.put()), greeting.author.nickname(), greeting.content, unicode(greeting.date)]

    def Del(self, *args):
        item = db.get(args[0])
        item.delete()
        return args[0]

#class Guestbook(webapp.RequestHandler):
#    def post(self):
#        greeting = Greeting()
#
#        if users.get_current_user():
#            greeting.author = users.get_current_user()
#
#        greeting.content = self.request.get('content')
#        greeting.put()
#        self.redirect('/')


#class Erase(webapp.RequestHandler):
#    def post(self):
#        target = self.request.get('key')
#        item = db.get(target)
#        item.delete()
#        self.redirect('/')


#application = webapp.WSGIApplication([('/', MainPage), ('/sign', Guestbook), ('/erase', Erase)], debug=True)


def main():
    application = webapp.WSGIApplication([('/', MainPage), ('/rpc', RPCHandler)], debug=True)
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()
