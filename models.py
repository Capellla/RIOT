__author__ = 'psakkaris'

"""
    This is the M part of MVC. Put all model definitions here
    and data access methods as well
"""
import datetime
import time
from google.appengine.ext import db

class InteractionGroup(db.Model):
    name = db.StringProperty(required=True)

# interaction items belong to Interaction groups
class InteractionItem(db.Model):
    name = db.StringProperty(required=True)

class Session(db.Model):
    observer = db.StringProperty(required=True)
    observee = db.StringProperty(required=True)
    date = db.DateTimeProperty(required=True)
    location = db.StringProperty(required=False)
    course = db.StringProperty(required=False)
    notes = db.TextProperty(required=False)


class SessionRecord(db.Model):
    interactionItem = db.ReferenceProperty(reference_class=InteractionItem, required=True)
    startTime = db.IntegerProperty(required=True)
    endTime = db.IntegerProperty()
    dateCreated = db.DateTimeProperty(required=True)


#######################
### Access Methods ####
#######################

""" Get an interaction group by name will return a list of results but should
    contain only one item
"""
def get_interaction_group_by_name(name):
    query = db.GqlQuery("SELECT * FROM InteractionGroup " +
                        "WHERE name = :1", name)
    return query.run()

""" Get all sessions started by a specific observer
"""
def get_sessions_for_user(user):
    if user:
        query = db.GqlQuery("SELECT * FROM Session " +
                            "WHERE observer = :1", user.email())
        return query.fetch(1000)
    else:
        return []

def deactivate_active_records_for_session(session):
    if session is not None:
        # TODO: can make this more efficient by querying which SessionRecord
        # dont have an endtime set but good enough for now
        sessionRecords = SessionRecord.all().ancestor(session).fetch(1000)
        for sr in sessionRecords:
            if sr.endTime is None or sr.endTime < 1:
                sr.endTime = int(time.time())
                sr.put()

def get_interaction_item(groupId, itemId):
    group = InteractionGroup.get_by_id(int(groupId))
    if group is not None:
        return InteractionItem.get_by_id(itemId, parent=group)
    else:
        return None

def activate_session_record(session, interactionItem):
    nowSecs = int(time.time())
    now = datetime.datetime.now()
    sessionRecord = SessionRecord(parent=session, interactionItem=interactionItem,
                                  startTime=nowSecs, dateCreated=now)
    sessionRecord.put()

