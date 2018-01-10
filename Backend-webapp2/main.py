import webapp2
import json
from google.appengine.api import users, oauth
from google.appengine.api import search
from google.appengine.ext import ndb

scope = ['https://www.googleapis.com/auth/userinfo.email']


def getRelation(myEmail,personEmail):
    rel = "UNKOWN"
    relStatus = ""
    q1 = Connection.query(Connection.student == myEmail, Connection.tutor == personEmail)
    for c in q1:
        relStatus = c.status
        rel = "STUDENT"
        return rel,relStatus
    q2 = Connection.query(Connection.tutor == myEmail, Connection.student == personEmail)
    for c in q2:
        relStatus = c.status
        rel = "TUTOR"
        return rel,relStatus
    return rel, relStatus


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
     student = ndb.StringProperty()
     tutor = ndb.StringProperty()
     message = ndb.StringProperty()
     status = ndb.StringProperty()

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
        connection = json.loads(self.request.body)
        email = getEmail(json.loads(self.request.body))
        id = connection.get('key')
        if (id):
           key = ndb.Key('Connection',id)
           con = key.get()
           con.status = connection['status']
           con.put()
        else:
            # create new connection request
            con = Connection(student=connection['student'],tutor=connection['tutor'],message=connection['message'],status=connection['status'])
            con.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(con.to_dict()))


class StudentsHandler(webapp2.RequestHandler):
    #Make scaleable in future with a cursor
    def get(self):
        email = getEmail(self.request)
        q1 = Connection.query(Connection.student == email,Connection.status == 'ACCEPTED')
        ans = []
        for c in q1:
            ans.append(c.to_dict())
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(ans))

class TutorsHandler(webapp2.RequestHandler):
    #Make scaleable in future with a cursor
    def get(self):
        email = getEmail(self.request)
        q1 = Connection.query(Connection.tutor == email,Connection.status == 'ACCEPTED')
        ans = []
        for c in q1:
            ans.append(c.to_dict())
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(ans))

class SearchHandler(webapp2.RequestHandler):
     def post(self):
          self.response.headers.add_header('Access-Control-Allow-Origin', '*')
          data = json.loads(self.request.body)
          myEmail = getEmail(json.loads(self.request.body))

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
                   rel,relStatus = getRelation(myEmail,prof.key.id())
                   p = prof.to_dict()
                   p['relationship'] = rel
                   p['relStatus'] = relStatus
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
    ('/Students', StudentsHandler),
    ('/Tutors', TutorsHandler)
], debug=True)
