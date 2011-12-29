#!/usr/bin/env python

"""
    Simple webapp2 piratepad-like rest editor with PDF exporting capabilities.
"""

import webapp2, jinja2, os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),
        'Templates')))

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
        return name # TODO

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
            template('pad.html', {
                'body': body,
                'messages': 'Created new pad %s' %(filter_name(name)})

    class GetRestPad(PadHandler):
        """
            Return an existing pad
        """
        def get(self, name):
            """
            """
            body = self.get_pad(name)
            if body:
                template('pad.html', {'body': body, 'messages': None})
            else:
                self.redirect('/new/%s', name)

    def SaveRestPad(PadHandler):
        """
            Save a rest pad revision.
        """
        def get(self, name):
            return #TODO save it (remember that it will just create a new revision)

    def ListRevisions(PadHandler):
        def get(self, name):
            return name # TODO: return revisions on a specific template.

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

