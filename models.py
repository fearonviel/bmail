from google.appengine.ext import ndb

class Message(ndb.Model):
    message = ndb.StringProperty()
    receiver = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    subject = ndb.StringProperty()
    deleted = ndb.BooleanProperty(default=False)
    sender_email = ndb.StringProperty()
    sender_name = ndb.StringProperty()
