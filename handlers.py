import models
import riot_utils
import webapp2
import json
import logging
import datetime

from google.appengine.api import users

"""
    This is the C part of MVC. Put all logic for controllers here. Url
    patterns will map to controllers defined in this module.
"""

# mappings for /
class HomeHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.write(riot_utils.render_template('templates/home.html', {
                'user': user,
                'test': 'loof'
            }))
        else:
            self.redirect(users.create_login_url(self.request.uri))

# mappings for /session/new
class NewSessionHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.write(riot_utils.render_template('templates/new_session.html', {}))
        else:
            self.redirect(users.create_login_url(self.request.uri))

    def post(self):
        user = users.get_current_user()
        observee = self.request.get('observee')
        logging.info("------ " + observee)
        course = self.request.get('course')
        location = self.request.get('location')

        if not user:
            self.response.write(json.dumps({'error': 'You must be logged in'}))
        if observee is None or not len(observee):
            self.response.write(json.dumps({'error': 'You must specify an observee'}))

        # checks pass, create new session
        session = models.Session(observee=observee, observer=user.email(), date=datetime.datetime.now())
        session.course = course
        session.location = location

        session.put()
        self.response.write(json.dumps({'session_id': session.key().id()}))

# mappings for /sessions
class SessionListHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            sessions = models.get_sessions_for_user(user)
            self.response.write(riot_utils.render_template('templates/sessions.html', {
                'sessions': sessions
            }))
        else:
            self.redirect(users.create_login_url(self.request.uri))

# mappings for /session/id
class SessionHandler(webapp2.RequestHandler):
    def get(self, sessionId):
        user = users.get_current_user()
        if user:
            session = models.Session.get_by_id(int(sessionId))
            if session and user.email() == session.observer:
                query = models.InteractionGroup.all()
                interactionGroups = query.run()
                interactions = []
                for interaction in interactionGroups:
                    interactionItems = models.InteractionItem.all().ancestor(interaction).fetch(1000)
                    interactions.append(InteractionGroupItems(interaction, interactionItems))

                self.response.write(riot_utils.render_template('templates/session.html', {
                    'session': session,
                    'interactions': interactions
                }))
            else:
                self.response.write({'error': 'invalid session id'})
        else:
            self.redirect(users.create_login_url(self.request.uri))


# /session/record/{sessionId} mapping
class SessionRecordHandler(webapp2.RequestHandler):
    def post(self, sessionId):
        user = users.get_current_user()
        if user:
            session = models.Session.get_by_id(int(sessionId))
            if not session:
                self.response.write({'error': 'no session with id: ' + sessionId})
                return
            if not session.observer == user.email():
                self.response.write({'error': 'not authorized'})
                return

            # checks pass
            models.deactivate_active_records_for_session(session)
            groupId = self.request.get('groupId')
            itemId = self.request.get('itemId')
            if is_blank(groupId):
                self.response.write({'error': 'You must provide an interaction group id'})
                return
            if is_blank(itemId):
                self.response.write({'error': 'You must provide an interaction item id'})
                return

            interactionItem = models.get_interaction_item(int(groupId), int(itemId))
            if interactionItem is None:
                self.response.write({'error': 'No iteraction item with groupId: ' + groupId +
                                              ' and itemId: ' + itemId})

            models.activate_session_record(session, interactionItem)
            self.response.write({'success': True})
        else:
            self.response.write({'error': 'must be logged in'})


# /session/stop/{sessionId} mapping
class StopSessionHandler(webapp2.RequestHandler):
    def post(self, sessionId):
        user = users.get_current_user()
        if user:
            session = models.Session.get_by_id(int(sessionId))
            if not session:
                self.response.write({'error': 'no session with id: ' + sessionId})
                return
            if not session.observer == user.email():
                self.response.write({'error': 'not authorized'})
                return

            # checks pass
            models.deactivate_active_records_for_session(session)
        else:
            self.response.write({'error': 'must be logged in'})


# mappings for /session/records/{sessionId}
class SessionRecordListHandler(webapp2.RequestHandler):
    def get(self, sessionId):
        user = users.get_current_user()
        if user:
            session = models.Session.get_by_id(int(sessionId))
            if session and session.observer == user.email():
                session_records = models.SessionRecord.all().ancestor(session).fetch(1000)
                for sr in session_records:
                    sr.totalSeconds = sr.endTime - sr.startTime

                self.response.write(riot_utils.render_template('templates/session_records.html', {
                    'session': session,
                    'session_records': session_records
                }))
            else:
                self.response.write({'error': 'invalid session id'})
        else:
            self.redirect(users.create_login_url(self.request.uri))


# mappings for /interactions
class InteractionListHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            query = models.InteractionGroup.all()
            interactionGroups = query.run()
            interactions = []
            for interaction in interactionGroups:
                interactionItems = models.InteractionItem.all().ancestor(interaction).fetch(1000)
                interactions.append(InteractionGroupItems(interaction, interactionItems))

            self.response.write(riot_utils.render_template('templates/interactions.html', {
                'user': user,
                'interactions': interactions
            }))
        else:
            self.redirect(users.create_login_url(self.request.uri))


# mappings for /interaction/group/new
class InteractionHandler(webapp2.RequestHandler):
    def post(self):
        name = self.request.get('name')
        results = models.get_interaction_group_by_name(name)
        print results.__dict__
        if len(list(results)):
            self.response.write(json.dumps({'error': 'Interaction group with name: ' + name + ' already exists'}))
        else:
            ig = models.InteractionGroup(name=name)
            ig.put()
            self.response.write(json.dumps(ig.__dict__))


# mappings for /interaction/item/new
class InteractionItemHandler(webapp2.RequestHandler):
    def post(self):
        parentId = self.request.get('parentId')
        name = self.request.get('name')
        if parentId is None or not len(parentId):
            self.response.write({'error': 'You must specify the parent id'})
            return
        if name is None or not len(name):
            self.response.write({'error': 'You must specify a name'})

        # grab parent interaction group
        parentGroup = models.InteractionGroup.get_by_id(int(parentId))
        if parentGroup is None:
            self.response.write({'error': 'No group with id ' + parentId})
        else:
            item = models.InteractionItem(parent=parentGroup, name=name)
            item.put()
            self.response.write(json.dumps({"success": True}))


###################################################################
#                   HELPER CLASSES
###################################################################

class InteractionGroupItems():
    def __init__(self, interactionGroup, interactionItems):
        self.group = interactionGroup
        self.items = interactionItems

###################################################################
#                  HELPER METHODS
###################################################################

def is_blank(str):
    return str is None or len(str) == 0