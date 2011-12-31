#!/usr/bin/env python

"""
    Simple webapp2 piratepad-like rest editor with PDF exporting capabilities.
    TODO: This still does not save anything in database.
    TODO: Make the templates
    TODO: Make the rst2pdf stuff.
"""
from google.appengine.ext import db
import webapp2, jinja2, os, logging
from google.appengine.ext.webapp.util import run_wsgi_app

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
        return name # TODO

    def get_pad(self, name, revision=False):
        """
            Returns pad revision
            @param name: Pad name (stripped)
            @type name: string
            @param revision: revision number of the pad
            @type revision: int
        """
        parent_pad = Pad.gql('where pad_name=:1', name).get()
        if revision: return parent_pad.revisions[revision]
        else:
            for i in parent_pad.revisions:
                return i

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
        logging.info(name)
        logging.info('Creating new template %s', name)
        try:
            pad = self.get_pad(name)
            if not pad:
                raise Exception("None")
        except Exception, e:
            pad = Pad(pad_name = name)
        pad.put()
        revision = PadRevision(pad_name = pad)
        revision.pad_text = "New pad %s\n ======================"\
             %(self.filter_name(name))
        logging.debug(pad.revisions.get())
        revision.put()

        self.redirect('/pad/' + name)

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
            logging.info(self.get_pad(name))
            body = self.get_pad(name, revision).pad_text
            self.template('pad.html', {'body': body, 'messages': None})
        except Exception, err:
            logging.info(err)
            # self.redirect('/new/%s', name)

class SaveRestPad(PadHandler):
    """
        Save a rest pad revision.
    """
    def get(self, name):
        PadRevision(pad = self.get_pad(name)) # Get lastest
        #self.redirect('/pad/%s' %(name))

class ListRevisions(PadHandler):
    def get(self, name):
        """
            Returns an unordered list of revisions of a pad.
        """
        self.out.write("<ul>")
        for pad in self.get_pad(name).revisions:
            self.out.write("<li>%s - %s</li>" %(pad.name, pad.date))
        self.out.write("</ul>")

class GetPdfPad(PadHandler):
    def get(self, name):
        self.response.headers['content-type'] = 'application/pdf'
        self.response.out.write(self.pdfy(name))

    def pdfy(self, name):
        return # TODO

run_wsgi_app(webapp2.WSGIApplication(
    [
        ('/new/(.*)', NewRestPad),
        ('/pad/(.*)', GetRestPad),
        ('/save/(.*)', SaveRestPad),
        ('/pad_revisions/(.*)', ListRevisions),
        ('/pdf/(.*)', GetPdfPad)
    ],
    debug=True))

