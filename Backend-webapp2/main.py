import webapp2
import json
import os
from google.appengine.api import users, oauth
from google.appengine.api import search
from google.appengine.ext import ndb
from oauth2client.client import GoogleCredentials

import httplib2
import requests
#from google.cloud import pubsub

projectID = "collabarter-188623"
scope = ['https://www.googleapis.com/auth/userinfo.email']


def getConnection(myEmail,personEmail):
    id = myEmail + '_' + personEmail
    con = Connection.get_by_id(id)
    if(con):
        return con
    id = personEmail + '_' + myEmail
    con = Connection.get_by_id(id)
    if(con):
        return con
    return None


#Relationship: student, tutor, both
#Status: NOT CONNECTED, PENDING, APPROVED


def getInvitation(myEmail,personEmail):
    inv = "NOT CONNECTED"
    q1 = Connection.query(Connection.me == personEmail, Connection.person == myEmail)
    for c in q1:
        if(c.status == 'PENDING'):
            return True
    return False

def getEmail(rd=None):
    #rd - self.request for GET
    # rd - json.loads(self.request.body) for POST
    user = oauth.get_current_user(scope)
    email = None
    if (user):
        email = user.email()
        if((email == "example@example.com") and (rd != None)):
            email = rd.get("email")
    if (email == ""):
        email = None
    return email


class ConnectionUtil(object):
    def to_dict(self):
        result = super(ConnectionUtil, self).to_dict()
        result['key'] = self.key.id()  # get the key as a string
        return result

class Connection(ConnectionUtil,ndb.Model):
     me = ndb.StringProperty()
     person = ndb.StringProperty()
     message = ndb.StringProperty()
     status = ndb.StringProperty()
     relationship = ndb.StringProperty()
     topic_name = ndb.StringProperty()
class Course(ndb.Model):
     email = ndb.StringProperty()
     name = ndb.StringProperty()
     description = ndb.StringProperty()
     @classmethod
     def _post_put_hook(self, future):
          fields=[search.TextField(name='name', value=self.name),
                  search.TextField(name='description', value=self.description),
                  search.TextField(name='email', value=self.email)
          ]
          print eval(self.key)
          doc = search.Document(doc_id=eval(self.key), fields=fields)
          index = search.Index('Course')
          index.put(doc)


class Profile(ndb.Model):
     firstname = ndb.StringProperty()
     lastname = ndb.StringProperty()
     gpa = ndb.FloatProperty()
     university = ndb.StringProperty()
     major = ndb.StringProperty()
     def _post_put_hook(self, future):
          fields=[search.TextField(name='firstname', value=self.firstname),
                  search.TextField(name='lastname', value=self.lastname),
                  search.NumberField(name='gpa', value=self.gpa),
				  search.TextField(name='university', value=self.university),
				  search.TextField(name='major', value=self.major),
          ]
          print self.key.id()
          doc = search.Document(doc_id=self.key.id(), fields=fields)
          index = search.Index('Profile')
          index.put(doc)

class ConnectionHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        connection = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        if (email == None):
            return
        con = getConnection(email,connection['person'])
        if(con):
            return
        #Connection type 1: me to tutor. {"person": personemail}
        #Connection type 2: me to student {"student": personemail}
        con = Connection(me=email, person=connection['person'], message=connection['message'],status="PENDING", relationship="NONE")
        con.key = ndb.Key(Connection, email + '_' + connection['person'])
        con.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(con.to_dict()))


    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class RemoveConnectionHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        connection = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        if(email == None):
            return
        # Connection type 1: me to tutor. {"tutor": personemail}
        # Connection type 2: me to student {"student": personemail}
        con = getConnection(email,connection['person'])
        if (con):
            con.key.delete()

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class RejectInvitationHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        connection = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        if(email == None):
            return
        # Connection type 1: me to tutor. {"tutor": personemail}
        # Connection type 2: me to student {"student": personemail}
        con = getConnection(email,connection['person'])
        if (con):
            con.key.delete()

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class ApproveInvitationHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        connection = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        if (email == None):
            return
        con = getConnection(email,connection['person'])
        if(con):
            con.status = "APPROVED"
            con.put()

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class StudentsHandler(webapp2.RequestHandler):

    #Make scaleable in future with a cursor
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        email = getEmail(self.request)
        if (email == None):
            return
        q1 = Connection.query(ndb.AND(Connection.me == email),(Connection.relationship.IN(['STUDENT','BOTH'])))

        ans = []
        profiles = []
        for c in q1:
            prof = Profile.get_by_id(c.person)
            print "In first loop"

            relStatus = c.status
            rel = c.relationship
            p = prof.to_dict()
            p['relStatus'] = relStatus
            p['email'] = c.person
            p['relationship'] = rel
            profiles.append(p)

        q2 = Connection.query(ndb.AND(Connection.person == email),(Connection.relationship.IN(['TUTOR','BOTH'])))
        for c in q2:
            print "In second loop"
            prof = Profile.get_by_id(c.me)
            relStatus = c.status
            rel = c.relationship
            if(rel == 'TUTOR'):
                rel = 'STUDENT'
            p = prof.to_dict()
            p['relStatus'] = relStatus
            p['email'] = c.me
            p['relationship'] = rel
            profiles.append(p)


        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(profiles))

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class TutorsHandler(webapp2.RequestHandler):
    # Make scaleable in future with a cursor
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        email = getEmail(self.request)
        if (email == None):
            return
        q1 = Connection.query(ndb.AND(Connection.me == email), (Connection.relationship.IN(['TUTOR', 'BOTH'])))

        ans = []
        profiles = []
        for c in q1:
            prof = Profile.get_by_id(c.person)
            print "In first loop"

            relStatus = c.status
            rel = c.relationship
            p = prof.to_dict()
            p['relStatus'] = relStatus
            p['email'] = c.person
            p['relationship'] = rel
            profiles.append(p)

        q2 = Connection.query(ndb.AND(Connection.person == email), (Connection.relationship.IN(['STUDENT', 'BOTH'])))
        for c in q2:
            print "In second loop"
            prof = Profile.get_by_id(c.me)
            relStatus = c.status
            rel = c.relationship
            if (rel == 'STUDENT'):
                rel = 'TUTOR'
            p = prof.to_dict()
            p['relStatus'] = relStatus
            p['email'] = c.me
            p['relationship'] = rel
            profiles.append(p)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(profiles))

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers[
            'Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class SearchHandler(webapp2.RequestHandler):
     def post(self):
          self.response.headers.add_header('Access-Control-Allow-Origin', '*')
          data = json.loads(self.request.body)
          myEmail = getEmail(json.loads(self.request.body))
          if(myEmail == None):
              return
          # {"search": "free text serach string"}

          # build query
          query_string = data['search']
          query_options = search.QueryOptions(limit=10)
          query = search.Query(query_string=query_string, options=query_options)

          # look up Profile documents
          index = search.Index('Profile')
          results = index.search(query)
          profiles = []
          for r in results:
               prof = Profile.get_by_id(r.doc_id)
               if (prof):
                   personEmail = prof.key.id()
                   relStatus = "NOT CONNECTED"
                   rel = "NONE"
                   con = getConnection(myEmail, personEmail)
                   if (con):
                       relStatus = con.status
                       rel = con.relationship
                       if (con.me != myEmail):
                           print "Swapping rels.."
                           if (rel == "STUDENT" ):
                               print "swapping from student..."
                               rel = "TUTOR"
                           elif (rel == "TUTOR"):
                               print "swapping from tutor..."
                               rel = "STUDENT"

                   p = prof.to_dict()
                   p['relStatus'] = relStatus
                   p['email'] = personEmail
                   inv = getInvitation(myEmail,personEmail)
                   p['invitation'] = inv
                   p['relationship'] = rel
                   profiles.append(p)

          #index = search.Index('Course')
          #results = index.search(query)
          #for r in results:
               #ans.append(r.doc_id)


          self.response.headers['Content-Type'] = 'application/json'
          self.response.write(json.dumps(profiles))

     def options(self):
          self.response.headers['Access-Control-Allow-Origin'] = '*'
          self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
          self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'


class CoursesHandler(webapp2.RequestHandler):
     def post(self):
          data = self.request.body
          email = getEmail(json.loads(self.request.body))
          if(email == None):
              msg = "invalid user"
              self.response.write(json.dumps(msg))
              return
          courses = json.loads(data)
          ents = []
          l = len(courses)
          for i in range(0,l):
               print courses[i]
               crs = Course(email=email,
                            name=courses[i]['name'],
                            description=courses[i]['description'])
               ents.append(crs)

          ndb.put_multi(ents)
          self.response.headers['Content-Type'] = 'application/json'
          self.response.write(data)

     def get(self):

          email = getEmail(self.request)
          if (email == None):
              return
          user = oauth.get_current_user()
          if user:
               print 'Hello ' + user.nickname()

          q1 = Course.query(Course.email == email)

          ans = []
          for c in q1:
               ans.append(c.to_dict())

          print ans
          self.response.headers['Content-Type'] = 'application/json'
          self.response.write(json.dumps(ans))




class ProfileHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        student = json.loads(self.request.body)
        print "Inside post ..."
        print student
        print "done printing"
        email = getEmail(json.loads(self.request.body))

        #email = student['email']
        if (email == None):
            msg = "invalid user"
            self.response.write(json.dumps(msg))
            return
        pro = Profile(firstname=student['firstname'],
                    lastname=student['lastname'],
                    gpa=student['gpa'],
					university=student['university'],
					major=student['major'])
        pro.key = ndb.Key(Profile, email)
        pro.put()

        self.response.write(json.dumps(pro.to_dict()))

    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        # get user email first

        myEmail = getEmail(self.request)
        #email = "shardoolpathak@gmail.com"
        if(myEmail == None):
            msg = "invalid user"
            self.response.write(json.dumps(msg))
            self.response.set_status(400)
            return
        print "inside GET Profile ...[" + myEmail + "]"
        pro = Profile.get_by_id(myEmail)
        if (pro):
            ans = pro.to_dict()
            print 'getting profile ...'
            print ans
            self.response.write(json.dumps(ans))
        else:
            self.response.write(json.dumps(""))
        #self.response.set_status(200)
        return

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'


class RelationshipHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        connection = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        if (email == None):
            return
        con = getConnection(email,connection['person'])
        if(con):
            rel = connection['relationship']
            print con.me
            if (con.me != email):
                print "Swapping rels"
                if (rel == 'STUDENT'):
                    print "swapping from student"
                    rel = 'TUTOR'
                elif (rel == 'TUTOR'):
                    print "swapping from tutor"
                    rel = 'STUDENT'

            con.relationship = rel
            con.put()

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'




class SendMessageHandler(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        msg = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        if (email == None):
            return
        con = getConnection(email, msg['person'])
        if(con == None):
            return
        if(con.status != "APPROVED"):
            return
        topic_name = con.topic_name
        if(topic_name == None):
            #Create new topic
            topic_name = "Chat " + email + '_' + msg['person']
            con.topic_name = topic_name
            con.put()
        #topic = self.create_topic(projectID,topic_name)

        #publisher = pubsub.PublisherClient()
        #publisher.publish(topic,msg['message'],writer=email)
        #POST https://pubsub.googleapis.com/v1/{topic}:publish
        u1 = "https://pubsub.googleapis.com/v1/projects/" + projectID + "/topics/" + topic_name + ":publish"
        credentials = GoogleCredentials.get_application_default()
        token = None
        http = httplib2.Http()

        if (credentials != None):
            credentials = credentials.create_scoped(PUBSUB_SCOPES)
            http = credentials.authorize(http)
        payload = {"messages": [{"data": msg['message']}, {"attributes": {"writer": email}}]}
        resp, content = http.request(uri=u1, method='POST', body=payload)
        self.response.write('message sent')

            #print credentials.to_json()
            ##credentials.refresh_token()
            #token = credentials.get_access_token()[0]
            #print 'access token : ' + token
        #headers = []
        #if (token):
        #    headers = {"Authorization": "Bearer " + token}
        #payload = {"messages": [{"data": msg['message']}, {"attributes": {"writer": email}}]}
        #req1 = requests.post(u1, headers=headers)
        #ans = json.loads(req1)

        #Post a message to this topic

    def create_topic(self, project, topic_name):
        #PUT https: // pubsub.googleapis.com / v1 /

        """Create a new Pub/Sub topic."""
        #publisher = pubsub.PublisherClient()
        #topic_path = publisher.topic_path(project, topic_name)

        #topic = publisher.create_topic(topic_path)
       # u1 =  "https://pubsub.googleapis.com/v1/projects/" + project + "/topics/" + topic_name
       # headers = ("Authorization": "Bearer ")
        #req1 = requests.put(u1,headers = headers)
        #ans = json.loads(req1)
       # topic = ans['name']
        #print('Topic created: {}'.format(topic))
        #return topic

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'

class PendingHandler(webapp2.RequestHandler):
    # Make scaleable in future with a cursor
    def get(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        email = getEmail(self.request)
        if (email == None):
            return
        q1 = Connection.query(ndb.AND(Connection.me == email), (Connection.status == "PENDING"))

        ans = []
        profiles = []
        for c in q1:
            prof = Profile.get_by_id(c.person)
            print "In first loop"

            relStatus = c.status
            rel = c.relationship
            p = prof.to_dict()
            p['relStatus'] = relStatus
            p['email'] = c.person
            p['relationship'] = rel
            profiles.append(p)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(profiles))

    def options(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers[
            'Access-Control-Allow-Headers'] = 'Authorization, Origin,  X-Requested-With, X-Auth-Token, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, DELETE'


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')


app = webapp2.WSGIApplication([
    ('/', MainPage),
     ('/Profile', ProfileHandler),
     ('/Courses', CoursesHandler),
     ('/Search', SearchHandler),
    ('/Connection', ConnectionHandler),
    ('/ApproveInvitation', ApproveInvitationHandler),
    ('/RejectInvitation', RejectInvitationHandler),
    ('/RemoveConnection', RemoveConnectionHandler),
    ('/ChangeRelation', RelationshipHandler),
    ('/Students', StudentsHandler),
    ('/Tutors', TutorsHandler),
    ('/PendingRequests', PendingHandler),
    ('/SendMessage', SendMessageHandler)

], debug=True)
