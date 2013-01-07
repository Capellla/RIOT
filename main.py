#!/usr/bin/env python

# Main class that starts the WSGI webb app
# and registers handlers

import webapp2
from handlers import HomeHandler, InteractionHandler, InteractionListHandler, \
    InteractionItemHandler, NewSessionHandler, SessionListHandler, SessionHandler, SessionRecordHandler, \
    StopSessionHandler, SessionRecordListHandler

# start app
app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/sessions', SessionListHandler),
    ('/session/new', NewSessionHandler),
    (r'/session/(\d+)', SessionHandler),
    (r'/session/record/(\d+)', SessionRecordHandler),
    (r'/session/records/(\d+)', SessionRecordListHandler),
    (r'/session/stop/(\d+)', StopSessionHandler),
    ('/interactions', InteractionListHandler),
    ('/interaction/group/new', InteractionHandler),
    ('/interaction/item/new', InteractionItemHandler)
], debug=True)
