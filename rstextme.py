#!/usr/bin/env python

"""
    Simple webapp2 piratepad-like rest editor with PDF exporting capabilities.
"""
from google.appengine.ext import db
import webapp2, jinja2, os

jinja_environment = jinja2.Environment( loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'Templates')))

class Pad(db.Model):
    """
        Collection of pad_revision objects
    """

    pad_name = db.StringProperty()

class PadRevision(db.Model):
    """
        Single revision of a pad
        Identifies itself to pad as pad.revisions.
    """
    pad_text = db.StringProperty()
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
        return name # TODO

    def get_pad(self, name, revision=False):
        """
            Returns pad revision
            @param name: Pad name (stripped)
            @type name: string
            @param revision: revision number of the pad
            @type revision: int
        """
        return Pad.gql('name=\'%s\'' %(name)).get()

class MainPage(object):
    """
        Main handler, will subclass all stuff for clarity (not really needed)
    """
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
            """
            self.template('pad.html', {
                'body': 'New pad %s\n======================',
                'messages': 'Created new pad %s' %(filter_name(name))})

    class GetRestPad(PadHandler):
        """
            Return an existing pad
        """
        def get(self, name):
            """
                Gets pad body, renders template.
                If no path body present redirects to /new/padname
            """
            try:
                body = self.get_pad(name).body
                self.template('pad.html', {'body': body, 'messages': None})
            except:
                self.redirect('/new/%s', name)

    def SaveRestPad(PadHandler):
        """
            Save a rest pad revision.
        """
        def get(self, name):
            PadRevision(pad = self.get_pad(name))
            self.redirect('/pad/%s' %(name))

    def ListRevisions(PadHandler):
        def get(self, name):
            for pad in self.get_pad(name).revisions:
                self.out.write("<li>%s - %s</li>" %(pad.name, pad.date))

    class GetPdfPad(PadHandler):
        def get(self, name):
            self.response.headers['content-type'] = 'application/pdf'
            self.response.out.write(self.pdfy(name))

        def pdfy(self, name):
            return # TODO

app = webapp2.WSGIApplication(
    [
        ('/new/(.*)', MainPage.NewRestPad),
        ('/pad/(.*)', MainPage.GetRestPad),
        ('/pdf/(.*)', MainPage.GetPdfPad)
    ],
    debug=True)

