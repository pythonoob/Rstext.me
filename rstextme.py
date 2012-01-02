#!/usr/bin/env python

"""
    Simple webapp2 piratepad-like rest editor with PDF exporting capabilities.
    TODO: Make the rst2pdf stuff.
"""
from google.appengine.ext import db
import webapp2, jinja2, os, logging, cgi
from google.appengine.ext.webapp.util import run_wsgi_app

class Pad(db.Model):
    """
        Collection of pad_revision objects under a same id (pad name)
    """
    pad_name = db.StringProperty()

class PadRevision(db.Model):
    """
        Single revision of a pad
        Identifies itself to pad as pad.revisions.
    """
    pad_text = db.StringProperty(multiline = True)
    pad_date = db.DateProperty()
    pad = db.ReferenceProperty(Pad, collection_name = 'revisions')

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
            if not get_revision:
                return parent_pad
            revisions = parent_pad.revisions.get()
        except:
            return False            

        if revision:
            return revisions[revision]
        else:
            try:
                return revisions[-1]
            except:
                return revisions

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

        if not pad:
            logging.debug('Pad does not exist. Making one')
            pad = Pad(pad_name = name)
            pad.put()

        revision = PadRevision(pad = pad.key())
        revision.pad_text = "New pad %s\n ======================"\
             %(self.filter_name(name))
        revision.put()

        self.redirect('/pad/' + name)

class ListAllPads(PadHandler):
    """
        Get a list of all created pads (like a TOC)
    """
    def get(self):
        pads = self.list_pads()
        for pad in self.list_pads():
           self.response.out.write( "<li><a href='/pad/%s'>%s</a></li>"\
               %(pad.pad_name, pad.pad_name))

class GetRestPad(PadHandler):
    """
       Return an existing pad
    """
    def get(self, name, revision=False):
        """
            Gets pad body, renders template.
            If no path body present redirects to /new/padname
        """
        try:
            body = self.get_pad(name, revision).pad_text
            self.template('pad.html', {
                 'body': body, 'messages': None, 'pad_id':name,
                 'pad_name':name.replace('_', ' ')})

        except Exception, err:
            self.redirect('/new/' + name)

class SaveRestPad(PadHandler):
    """
        Save a rest pad revision.
    """
    def get(self, name):
        pad = self.get_pad(name, get_revision = False)
        revision = PadRevision(pad = pad)
        revision.put()
        self.redirect('/pad/' + name)

class ListRevisions(PadHandler):
    def get(self, name):
        """
            Returns an unordered list of revisions of a pad.
        """
        self.response.out.write("<ul>")
        pad = self.get_pad(name, get_revision = False)
        for padr in pad.revisions:
            self.response.out.write("<li>%s - %s</li>" %(pad.pad_name, padr.pad_date))
        self.response.out.write("</ul>")

class GetPdfPad(PadHandler):
    def get(self, name):
        self.response.headers['content-type'] = 'application/pdf'
        self.response.out.write(self.pdfy(name))

    def pdfy(self, name):
        return # TODO

if __name__ == "__main__":
    jinja_loader = jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), 'Templates'))
    jinja_environment = jinja2.Environment( loader = jinja_loader )

    run_wsgi_app(webapp2.WSGIApplication(
        [
            ('/pad/(.*)', GetRestPad),
            ('/pdf/(.*)', GetPdfPad),
            ('/new/(.*)', NewRestPad),
            ('/save/(.*)', SaveRestPad),
            ('/list', ListAllPads),
            ('/pad_revisions/(.*)', ListRevisions),
    
        ],
        debug=True))
