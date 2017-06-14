#!/usr/bin/env python
import os
import jinja2
import webapp2
from models import Message
import cgi
from google.appengine.api import users
import json
from google.appengine.api import urlfetch
from datetime import date
from datetime import timedelta
import calendar

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        return self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        return self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        user = users.get_current_user()
        params["user"] = user

        if user:
            logged_in = True
            logout_url = users.create_logout_url('/')
            params["logout_url"] = logout_url
        else:
            logged_in = False
            login_url = users.create_login_url('/')
            params["login_url"] = login_url

        params["logged_in"] = logged_in

        template = jinja_env.get_template(view_filename)
        return self.response.out.write(template.render(params))


class MainHandler(BaseHandler):
    def get(self):
        return self.render_template("home.html")


class NewmessageHandler(BaseHandler):
    def get(self):
        return self.render_template("newmessage.html")


class RezultatHandler(BaseHandler):
    def post(self):
        newmessage = cgi.escape(self.request.get("message"))
        receiver = cgi.escape(self.request.get("receiver"))
        subject = cgi.escape(self.request.get("subject"))
        sender_email = users.get_current_user().email()
        sender_name = users.get_current_user().nickname()

        message = Message(message=newmessage, receiver=receiver, subject=subject, sender_email=sender_email, sender_name=sender_name)
        message.put()

        return self.redirect_to("inbox")


class InboxHandler(BaseHandler):
    def get(self):
        receiver = users.get_current_user().email()
        messages = Message.query(Message.deleted == False, Message.receiver == receiver).order(-Message.date).fetch()
        params = {"messages": messages}

        return self.render_template("inbox.html", params=params)


class SentMessagesHandler(BaseHandler):
    def get(self):
        sender_email = users.get_current_user().email()
        messages = Message.query(Message.deleted == False, Message.sender_email == sender_email).order(-Message.date).fetch()
        params = {"messages": messages}

        return self.render_template("sent_messages.html", params=params)


class SingleMessageHandler(BaseHandler):
    def get(self, message_id):
        message = Message.get_by_id(int(message_id))
        params = {"message": message}
        return self.render_template("single_message.html", params=params)


class DeleteMessageHandler(BaseHandler):
    def post(self, message_id):
        message = Message.get_by_id(int(message_id))
        message.deleted = True
        message.put()
        return self.redirect_to("inbox")


class DeletedMessagesHandler(BaseHandler):
    def get(self):
        receiver = users.get_current_user().email()
        messages = Message.query(Message.deleted == True, Message.receiver == receiver).order(-Message.date).fetch()    #DODAJ DELETED ZA MESSAGES IZ SENT KATEGORIJE
        params = {"messages": messages}

        return self.render_template("deleted_messages.html", params=params)


class PermanentDeleteHandler(BaseHandler):
    def post(self, message_id):
        message = Message.get_by_id(int(message_id))
        message.key.delete()
        return self.redirect_to("inbox")


class RestoreMessageHandler(BaseHandler):
    def post(self, message_id):
        message = Message.get_by_id(int(message_id))
        message.deleted = False
        message.put()

        return self.redirect_to("inbox")


class CalendarHandler(BaseHandler):
    def get(self):
        return self.render_template("calendar.html")


class WeatherHandler(BaseHandler):
    def get(self):
        url = "http://api.openweathermap.org/data/2.5/forecast/daily?q=Ljubljana,705&cnt=4&units=metric&appid=124432c8173570a80330f686019a3bb0"
        url2 = "http://api.openweathermap.org/data/2.5/weather?q=Ljubljana&units=metric&appid=124432c8173570a80330f686019a3bb0"
        result = urlfetch.fetch(url)
        result2 = urlfetch.fetch(url2)
        weather = json.loads(result.content)
        current = json.loads(result2.content)

        #Days of the week
        first = date.today() + timedelta(days=1)
        first_day = first.strftime('%d. %m. %Y')
        today = calendar.day_name[first.weekday()]
        second = date.today() + timedelta(days=2)
        second_day = second.strftime('%d. %m. %Y')
        day2 = calendar.day_name[second.weekday()]
        third = date.today() + timedelta(days=3)
        third_day = third.strftime('%d. %m. %Y')
        day3 = calendar.day_name[third.weekday()]

        params = {"weather": weather, "current": current, "today": today, "day2": day2, "day3": day3, "first": first_day, "second": second_day, "third": third_day}

        return self.render_template("weather.html", params=params)

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler),
    webapp2.Route('/inbox', InboxHandler, name="inbox"),
    webapp2.Route('/sentmessages', SentMessagesHandler),
    webapp2.Route('/newmessage', NewmessageHandler),
    webapp2.Route('/rezultat', RezultatHandler),
    webapp2.Route('/inbox/<message_id:\d+>', SingleMessageHandler),
    webapp2.Route('/inbox/<message_id:\d+>/delete', DeleteMessageHandler),
    webapp2.Route('/deletedmessages', DeletedMessagesHandler),
    webapp2.Route('/inbox/<message_id:\d+>/permanentdelete', PermanentDeleteHandler),
    webapp2.Route('/inbox/<message_id:\d+>/restoremessage', RestoreMessageHandler),
    webapp2.Route('/calendar', CalendarHandler),
    webapp2.Route('/weather', WeatherHandler),
], debug=True)
