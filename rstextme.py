#!/usr/bin/env python

"""
    Simple webapp2 piratepad-like rest editor with PDF exporting capabilities.
    TODO: Make the rst2pdf stuff.
"""
from google.appengine.ext import db
from google.appengine.api import users
import webapp2, jinja2, os, logging, cgi
from datetime import datetime
from google.appengine.ext.webapp.util import run_wsgi_app

class Pad(db.Model):
    """
        Collection of pad_revision objects under a same id (pad name)
    """
    pad_name = db.StringProperty()
    is_private = db.BooleanProperty()
    user = db.UserProperty()

class PadRevision(db.Model):
    """
        Single revision of a pad
        Identifies itself to pad as pad.revisions.
    """
    pad_text = db.StringProperty(multiline = True)
    pad_date = db.DateTimeProperty(auto_now=True)
    pad = db.ReferenceProperty(Pad, collection_name = 'revisions')

def create_ul(elements):
    return "<ul>" + '\n'.join(["<li>%s</li>" %(element)\
            for element in elements ]) + "</ul>"

def get_template(template):
    """
        Returns a jinja template
    """
    return jinja_environment.get_template(template)

class PadHandler(webapp2.RequestHandler):
    """
        RequestHandler class to add template and filter_name support
    """
    def template(self, template, values):
        """
            @param template: filename of the template to load
            @type template: string
            @param values: values to pass to the template
            @type values: dict
            @returns: None

            Renders a template

        """
        self.response.out.write(get_template(template).render(values))

    def filter_name(self, name):
        """
            @param name: name to return filtered
            @type name: string
            @returns: string

            Filters out special characters from a name

            >>> PadHandler().filter_name('foo bar baz+stuff\'')
            foo_bar_baz+stuff

        """
        return cgi.escape(name.replace(' ', '_'))

    def list_pads(self):
        return Pad.all()

    def get_pad(self, name, revision = False, get_revision = True):
        """
            Returns pad revision
            @param name: Pad name (stripped)
            @type name: string
            @param revision: revision number of the pad
            @type revision: int
        """

        try:
            parent_pad = Pad.gql('where pad_name=:1', name).get()
            if not parent_pad:
                raise Exception("No pad found for %s" %(name))
            if not get_revision:
                return parent_pad

        except Exception, error:
            logging.info(error)
            return Pad(pad_name = name)

        if revision:
            return PadRevision.get_by_id(revision)
        else:
            return parent_pad.revisions.order('-pad_date').get()

class NewRestPad(PadHandler):
    """
        Create new pad on database
    """
    def get(self, name):
        """
            @param name: template name (and therefore id) to load
            @type name: string
            @returns None
            Prints the pad template rendered with a created new <pad> message
            TODO: This might cause collisions between users.
                 But it will be rare so it's ok right now
        """

        pad = self.get_pad(name)
        is_private = self.request.get('private')
        if is_private == "":
            is_private = True
        pad.is_private = is_private
        pad.put() # Update pad.

        revision = PadRevision(pad = pad.key())
        revision.pad_text = "New pad %s\n ======================"\
             %(self.filter_name(name))
        revision.put()
        logging.debug("Created new pad, redirecting.")
        self.redirect('/pad/' + name)

class ListAllPads(PadHandler):
    """
        Get a list of all created pads (like a TOC)
    """
    def get(self):
        pads = self.list_pads()
        body = create_ul(["<a href='/pad/%s'>%s</a>" %(pad.pad_name,
            pad.pad_name) for pad in self.list_pads()])
        self.template('pad_list.html', {'body': body, 'messages': None})

class GetRestPad(PadHandler):
    """
       Return an existing pad
    """
    def get(self, name, revision=False):
        """
            Gets pad body, renders template.
            If no path body present redirects to /new/padname
        """

        pad = self.get_pad(name, revision)
        parent_pad = self.get_pad(name, get_revision = False)
        if parent_pad.is_private and\
                not parent_pad.user == users.get_current_user():
            self.template('pad.html', {
                messages: 'You don\'t have access to this pad' })
            return 
        try:
            self.template('pad.html', {
                 'body': pad.pad_text, 'messages': None, 'pad_id':name,
                 'pad_name':name.replace('_', ' ')})

        except Exception, err:
            logging.debug("Something happend getting pad. Creating one")
            logging.debug(err)
            self.redirect('/new/' + name)

class SaveRestPad(PadHandler):
    """
        Save a rest pad revision.
    """
    def post(self, name):
        if pad.is_private and not pad.user == users.get_current_user():
            self.template('pad.html', {
                messages: 'You don\'t have access to this pad' })
            return 
        pad = self.get_pad(name, get_revision = False)
        revision = PadRevision(pad = pad)
        revision.pad_text = self.request.get('text')
        revision.put()
        self.redirect('/pad/' + name)

class ListRevisions(PadHandler):
    def get(self, name):
        """
            Returns an unordered list of revisions of a pad.
        """
        pad = self.get_pad(name, get_revision = False)
        body = create_ul(["<a href='/pad/%s/%s'>%s - %s</a>" %(pad.pad_name,
            padr.key().id(), pad.pad_name, padr.pad_date)\
            for padr in pad.revisions ])
        self.template('pad_list.html', {'body': body,
            'messages': "Warning: This information may be changing right now"})

class GetHtmlPad(PadHandler):
    def get(self, name):
        self.response.out.write(self.htmlfy(name))

    def htmlfy(self, name):
        from docutils import core
        from docutils.core import publish_parts
        os.environ['DOCUTILSCONFIG'] = ''
        messages = None

        try:
            parts = publish_parts(source = self.get_pad(name).pad_text,
                writer_name = 'html4css1',
                settings_overrides={'style':'colorful', 'config': None})
            return parts['whole'] # TODO Still not working
        except Exception, error:
            body = self.get_pad(name).pad_text
            self.template('pad.html', {
                 'body': body, 'messages': error, 'pad_id':name,
                 'pad_name':name.replace('_', ' ')})

class GetPdfPad(PadHandler):
    def get(self, name):
        self.response.headers['content-type'] = 'application/pdf'
        self.response.out.write(self.pdfy(name))

    def pdfy(self, name):
        return # TODO

class Landing(PadHandler):
    def get(self):
        self.template('index.html', {})

if __name__ == "__main__":
    jinja_loader = jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'Templates'))
    jinja_environment = jinja2.Environment( loader = jinja_loader )

    run_wsgi_app(webapp2.WSGIApplication(
        [
            ('/pad/(.*)/(.*)', GetRestPad),
            ('/', Landing),
            ('/pad/(.*)', GetRestPad),
            ('/pdf/(.*)', GetPdfPad),
            ('/html/(.*)', GetHtmlPad),
            ('/new/(.*)', NewRestPad),
            ('/save/(.*)', SaveRestPad),
            ('/list', ListAllPads),
            ('/pad_revisions/(.*)', ListRevisions),
    
        ],
        debug=True))
