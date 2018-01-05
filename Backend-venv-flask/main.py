

from google.appengine.api import users
from google.appengine.api import search
from google.appengine.ext import ndb
from flask import Flask, request, jsonify
from flask_cores import CORS
from utils import convert_to_dict


app = Flask(__name__)
CORS(app, supports_credentials=True)

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

@app.route('/', methods=['GET', 'POST'])
def main_method():
    return jsonify("hello from backend"), 200

@app.route('/Connection', methods=['POST'])
def Connection():
    if (request.method == 'POST'):
        connection = json.loads(self.request.body)
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

        return jsonify(con.to_dict()), 200

@app.route('/Students', methods=['GET'])
def Students():
    if (request.method == 'GET'):
        email = "a@g.com"
        q1 = Connection.query(Connection.student == email,Connection.status == 'ACCEPTED')
        ans = []
        for c in q1:
            ans.append(c.to_dict())

        return jsonify(ans), 200

@app.route('/Students', methods=['GET'])
def Tutors():
#class TutorsHandler(webapp2.RequestHandler):
    #Make scaleable in future with a cursor
    if (request.method == 'GET'):
        email = "a@g.com"
        q1 = Connection.query(Connection.tutor == email,Connection.status == 'ACCEPTED')
        ans = []
        for c in q1:
            ans.append(c.to_dict())

        return jsonify(ans), 200

@app.route('/Search', methods=['POST'])
#class SearchHandler(webapp2.RequestHandler):
def Search():
    if (request.method == 'POST'):
          data = request.get_json()
          # {"search": "free text serach string"}
          # build query
          query_string = data['search']
          query_options = search.QueryOptions(limit=10)
          query = search.Query(query_string=query_string, options=query_options)

          # look up Profile documents
          index = search.Index('Profile')
          results = index.search(query)
          ans = []
          for r in results:
               ans.append(r.doc_id)

          index = search.Index('Course')
          results = index.search(query)
          for r in results:
               ans.append(r.doc_id)

          return jsonify(ans), 200

@app.route('/Courses', methods=['POST', 'GET'])
def Courses():
     if (request.method == 'POST'):
          email = 'a@g.com'
          courses = request.get_json()
          ents = []
          l = len(courses)
          for i in range(0,l):
               print courses[i]
               crs = Course(email=email,
                            name=courses[i]['name'],
                            description=courses[i]['description'])
               ents.append(crs)
          
          ndb.put_multi(ents)

          return jsonify(ents), 200

     if (request.method == 'GET'):
          email = "a@g.com"
          user = users.get_current_user()
          if user:
               print 'Hello ' + user.nickname()
               
          q1 = Course.query(Course.email == email)
          
          ans = []
          for c in q1:
               ans.append(c.to_dict())

          print ans
          return jsonify(ans), 200
               
          
@app.route('/Profile', methods=['POST', 'GET'])
def Profile():
    if (request.method == 'POST'):

         student = request.get_json()
         pro = Profile(firstname=student['firstname'],
                      lastname=student['lastname'],
                      gpa=student['gpa'],
					  university=student['university'],
					  major=student['major'])
         pro.key = ndb.Key(Profile, student['email'])
         pro.put()

         return jsonify(pro.to_dict()), 200

    if (request.method == 'GET'):
        # get user email first
        user = users.get_current_user()
        print "inside GET Profile"
        if user:
            email = user.email()
            print email
        else:
            return jsonify("invalid user"), 500

        pro = Profile.get_by_id(email)
        ans = pro.to_dict()
        print 'getting profile ...'
        print ans
        return jsonify(ans), 200
         



