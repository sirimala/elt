from flask import Flask, flash, redirect, render_template, \
     request, jsonify, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from cerberus import Validator
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSON
from functools import wraps
from datetime import datetime
import time
import json
import os
from settings import APP_STATIC_JSON
from random import shuffle
import cgi
from werkzeug.utils import secure_filename
from flask import json as fJson
import logging
from logging.handlers import RotatingFileHandler
from config import BaseConfig
import uuid
import base64
from flask_mail import Mail, Message
import requests
import hashlib

app = Flask(__name__, static_url_path='')
mail=Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'xxxxx@gmail.com'
app.config['MAIL_PASSWORD'] = 'xxxxx'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
app.config['UPLOAD_FOLDER'] = APP_STATIC_JSON

app.debug_log_format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
# logHandler = logging.FileHandler('logs/login.log')
logHandler = RotatingFileHandler('logs.log', maxBytes=10000, backupCount=1)
# logHandler.setFormatter(formatter)
logHandler.setLevel(logging.NOTSET)
app.logger.addHandler(logHandler)
app.logger.setLevel(logging.NOTSET)
app.logger.info('Log message')
login_log = app.logger

app.secret_key = "some_secret"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/GCT'
app.config.from_object(BaseConfig)

app.debug = True

db = SQLAlchemy(app)

# formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# def setup_logger(name, log_file, level=logging.DEBUG):
#     handler = logging.FileHandler(log_file)        
#     handler.setFormatter(formatter)
#     logger = logging.getLogger(name)
#     logger.setLevel(level)
#     logger.addHandler(handler)
#     return logger

# login_log = setup_logger('login_logger', 'logs/login.log')

ALLOWED_EXTENSIONS = set(['json'])
QP_TEMPLATE_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'section': {
        'type': 'list', 'minlength': 1, 'required': True,
        'schema': {
            'type': 'dict', 
            'schema': {
                'name': {'type': 'string', 'required': True}, 
                'subsection': {
                    'type': 'list', 'minlength': 1, 'required': True,
                    'schema': {
                        'type': 'dict', 
                        'schema': {
                            'name': {'type': 'string', 'required': True},
                            'count': {'type': 'string', 'required': True},
                            'questions': {'type': 'list', 'maxlength': 0, 'required': True},
                            'note': {'type': 'string', 'required': True},
                            'types': {'type': 'string', 'required': True, 'allowed': ['video', 'record', 'passage', 'essay']},
                        }
                    }
                }
            }
        }
    }
}

RECORD_TYPE_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'questions': {
        'type': 'list', 'minlength': 1, 'required': True,
        'schema': {
            'type': 'dict', 
            'schema': {
                'question': {'type': 'string', 'required': True}, 
                'options': {'type': 'list', 'maxlength': 0, 'required': True},
                'id': {'type': 'string', 'required': True},
            }
        }
    },
    'note': {'type': 'string', 'required': True},
    'types': {'type': 'string', 'required': True, 'allowed': ['record']},
}

ESSAY_TYPE_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'questions': {
        'type': 'list', 'minlength': 1, 'required': True,
        'schema': {
            'type': 'dict', 
            'schema': {
                'question': {'type': 'string', 'required': True}, 
                'options': {'type': 'list', 'maxlength': 0, 'required': True},
                'id': {'type': 'string', 'required': True},
            }
        }
    },
    'note': {'type': 'string', 'required': True},
    'types': {'type': 'string', 'required': True, 'allowed': ['essay']},
}

PASSAGE_TYPE_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'types': {'type': 'string', 'required': True, 'allowed': ['passage']},
    'passageArray': {
        'type': 'list', 'minlength': 1, 'required': True,
        'schema': {
            'type': 'dict', 
            'schema': {
                'note': {'type': 'string', 'required': True},
                'passage': {'type': 'string', 'required': True},
                'questions': {
                    'type': 'list', 'minlength': 1, 'required': True,
                    'schema': {
                        'type': 'dict', 
                        'question': {'type': 'string', 'required': True},
                        'options': {'type': 'list', 'minlength': 4, 'required': True},
                        'id': {'type': 'string', 'required': True},
                        'answer': {'type': 'string', 'required': True},
                        'practicelinks': {'type': 'list', 'minlength': 0, 'required': True},
                    }
                }
            }
        }
    }
}

VIDEO_TYPE_SCHEMA = {
    'name': {'type': 'string', 'required': True},
    'types': {'type': 'string', 'required': True, 'allowed': ['passage']},
    'note': {'type': 'string', 'required': True},
    'videoArray': {
        'type': 'list', 'minlength': 1, 'required': True,
        'schema': {
            'type': 'dict', 
            'schema': {
                'link': {'type': 'string', 'required': True},
                'questions': {
                    'type': 'list', 'minlength': 1, 'required': True,
                    'schema': {
                        'type': 'dict', 
                        'question': {'type': 'string', 'required': True},
                        'options': {'type': 'list', 'minlength': 4, 'required': True},
                        'id': {'type': 'string', 'required': True},
                        'answer': {'type': 'string', 'required': True},
                        'practicelinks': {'type': 'list', 'minlength': 0, 'required': True},
                    }
                }
            }
        }
    }
}

validate_qp_template = Validator(QP_TEMPLATE_SCHEMA)
validate_passage_template = True
validate_video_template = True
validate_essay_template = Validator(ESSAY_TYPE_SCHEMA)
validate_record_template = Validator(RECORD_TYPE_SCHEMA)

schema_type_mapping = {
    'essay' :validate_essay_template,
    'record' :validate_record_template,
    'passage' :validate_record_template,
    'video' :validate_record_template,
}

e1_start=801;e1_end=809;e2_start=1201;e2_end=1208;e3_start=1601;e3_end=1701;
e4_start=1701;e4_end=1702;
global status
global errortype

def to_pretty_json(value):
    return json.dumps(value, sort_keys=True, indent=4, separators=(',', ': '))

app.jinja_env.filters['tojson_pretty'] = to_pretty_json

#A list of uri for each role
permissions_object = {
    'student':[
        '/',
        '/student'
    ],
    'admin':[
        '/',
        '/student',
        '/admin'
    ]}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    emailid = db.Column(db.String(180), unique=True)
    pin = db.Column(db.String(80))
    testctime = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name, pin, emailid):
        self.name = name
        self.pin = pin
        self.emailid = emailid

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emailid = db.Column(db.String(180), unique=True)
    password = db.Column(db.String(80))
    user_type = db.Column(db.String(10), default="student")
    verified = db.Column(db.String(80), default=False)
    registered_time = db.Column(db.DateTime(), default=datetime.utcnow)
    password_last_time = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, emailid, password, user_type, verified):
        self.emailid = emailid
        self.password = password
        self.user_type = user_type
        self.verified = verified

class AdminDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(180), unique=True, default="vy@fju.us")
    password = db.Column(db.String(1000), default="veda1997")

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def __repr__(self):
        return str(self.password)

class Students(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    emailid = db.Column(db.String(180), unique=True)
    rollno = db.Column(db.String(80))

    def __init__(self, name, emailid, rollno):
        self.name = name
        self.emailid = emailid
        self.rollno = rollno

    def __repr__(self):
        return str(self.name)+"::"+str(self.emailid)+"::"+str(self.rollno)

class Tests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    hosting_date = db.Column(db.String(80))
    # json = db.Column(db.String(1000))
    creator = db.Column(db.String(180))
    time = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name, creator, hosting_date):
        self.name = name
        self.creator = creator
        self.hosting_date = hosting_date
        self.time = datetime.utcnow()
        # self.json = json
    def isHosted(self):
        today = datetime.now()
        return datetime.strptime(self.hosting_date, '%d/%m/%Y') == today

    def __repr__(self):
        return str(self.name)+"::"+str(self.hosting_date)+"::"+str(self.creator)

class StudentTests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emailid = db.Column(db.String(180), unique=True)
    testslist = db.Column(ARRAY(db.String(80)))

    def __init__(self, emailid, testslist):
        self.emailid = emailid
        self.testslist = testslist

    def getTests(self):
        return self.testslist

class UserAudio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80))
    blob1 = db.Column(db.LargeBinary)
    time = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user, blob1):
        self.user = user
        self.blob1 = blob1

class DataModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(180))
    blob = db.Column(db.LargeBinary)

    def __init__(self, url, blob):
        self.url = url
        self.blob = blob 

class userDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email=db.Column(db.String(120), unique=True)
    phno = db.Column(db.String(120))
    rollno = db.Column(db.String(120))
    learningcenter = db.Column(db.String(120))

    def __init__(self, name, email, phno, rollno, learningcenter):
        self.name = name 
        self.email = email 
        self.phno = phno 
        self.rollno = rollno 
        self.learningcenter = learningcenter 

class TestDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(120))
    test= db.Column(db.Boolean())
    teststime=db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    delays=db.Column(db.Float())
    testend= db.Column(db.Boolean())
    lastPing = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    score = db.Column(db.Integer())
    learningcenter = db.Column(db.String(120))

    def __init__(self, **kwargs):
        super(TestDetails, self).__init__(**kwargs)

class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    emailid = db.Column(db.String(180))
    pin = db.Column(db.String(80))
    testctime = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    submittedans = db.Column(db.Text)
    responsetime = db.Column(db.Float)
    q_score = db.Column(db.Integer)
    q_status = db.Column(db.String(120))
    time = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow )
    currentQuestion=db.Column(db.String(120))
    serialno=db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(Response, self).__init__(**kwargs)

class Randomize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1=db.Column(db.String(120))
    serialno=db.Column(db.Integer)
    qno=db.Column(db.String(120))

    def __init__(self, user1, serialno, qno):
        self.user1 = user1 
        self.serialno = serialno 
        self.qno = qno 

class EssayTypeResponse(db.Model):
    """Sub model for storing user response for essay type questions"""
    id = db.Column(db.Integer, primary_key=True)
    useremailid = db.Column(db.String(120))
    qid = db.Column(db.String(120))
    ansText = db.Column(db.Text)
    qattemptedtime = db.Column(db.Float)

    def __init__(self, useremailid, qid, ansText, qattemptedtime):
        self.useremailid = useremailid 
        self.qid = qid 
        self.ansText = ansText 
        self.qattemptedtime = qattemptedtime 

def getQuestionPaper(qid_list):
    path = 'QP_template.json'
    json_temp=json.loads(open(os.path.join(APP_STATIC_JSON,path)).read())
    #print qid_list
    i=0;j=0;k=0;l=0;m=0;n=0;p=0;q=0;r=0;s=0;t=0
    for qid in qid_list:
        qid=int(qid)
        if qid in range(e1_start,e1_end):
              e1_readjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E1-Reading.json')).read())
              for key in e1_readjson["passageArray"]:
                    for qn in key["questions"]:
                          pid=qn["id"]
                          if int(pid) == qid:
                                json_temp["section"][1]["subsection"][0]["passage"]=key["passage"]
                                json_temp["section"][1]["subsection"][0]["questions"].append(qn)
                                json_temp["section"][1]["subsection"][0]["questions"][m]["serialno"] = qid_list[qid]
                                m +=1
        if qid in range(e2_start,e2_end):
              e2_lsnjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E2-Listening.json')).read())
              for key in e2_lsnjson["videoArray"]:
                    for qn in key["questions"]:
                          pid=qn["id"]
                          if int(pid) == qid:
                                json_temp["section"][0]["subsection"][0]["link"]=key["link"]
                                json_temp["section"][0]["subsection"][0]["questions"].append(qn)
                                json_temp["section"][0]["subsection"][0]["questions"][n]["serialno"] = qid_list[qid]
                                n +=1
        if qid in range(e3_start,e3_end):
              e3_spkjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E3-Speaking.json')).read())
              for key in e3_spkjson["questions"]:
                    if int(key["id"]) == qid:
                          json_temp["section"][0]["subsection"][1]["questions"].append(key)
                          json_temp["section"][0]["subsection"][1]["questions"][p]["serialno"] = qid_list[qid]
                          p += 1
        if qid in range(e4_start,e4_end):
              e4_wrtjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E4-Writing.json')).read())
              for key in e4_wrtjson["questions"]:
                    if int(key["id"]) == qid:
                          json_temp["section"][1]["subsection"][1]["questions"].append(key)
                          json_temp["section"][1]["subsection"][1]["questions"][q]["serialno"] = qid_list[qid]
                          q += 1
    return json_temp

def generateQuestionPaper():
    path = 'QP_template.json'
    json_temp=json.loads(open(os.path.join(APP_STATIC_JSON,path)).read())
    for key in json_temp:
        if  key == "section":
            section=json_temp[key]
            for s in section:
                for key in s:
                    if key == "subsection":
                        for subs in s[key]:
                            cnt=int(subs["count"])
                            name=subs["name"]
                            types=subs["types"]
                            #print name
                            if name == "E2-Listening":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                video_list=json_subs["videoArray"]
                                serialno=range(0,len(video_list))
                                shuffle(serialno)
                                subs["link"]=video_list[serialno[0]]["link"]
                                subs["questions"]=video_list[serialno[0]]["questions"]
                                i=0
                                for qn in subs["questions"]:
                                    subs["questions"][i]["serialno"]=i+1
                                    i +=1
                            if types =="question" or types =="record":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                qns_list=json_subs["questions"];
                                serialno=range(0,len(qns_list))
                                shuffle(serialno)
                                for no in range(0,cnt):
                                    subs["questions"].append(qns_list[serialno[no]])
                                    subs["questions"][no]["serialno"]=no+1
                            if types == "passage":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                psglist=json_subs["passageArray"]
                                serialno=range(0,len(psglist))
                                shuffle(serialno)
                                subs["questions"]=psglist[serialno[0]]["questions"]
                                j=0
                                for qn in subs["questions"]:
                                    subs["questions"][j]["serialno"]=j+1
                                    j +=1
                                subs["passage"]=psglist[serialno[0]]["passage"]
                            if types =="essay":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                qns_list=json_subs["questions"];
                                serialno=range(0,len(qns_list))
                                shuffle(serialno)
                                for no in range(0,cnt):
                                    subs["questions"].append(qns_list[serialno[no]])
                                    subs["questions"][no]["serialno"]=no+1
                            if name == "T2-Listening":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                video_list=json_subs["videoArray"]
                                serialno=range(0,len(video_list))
                                shuffle(serialno)
                                subs["link"]=video_list[serialno[0]]["link"]
                                subs["questions"]=video_list[serialno[0]]["questions"]
                                k=0
                                for qn in subs["questions"]:
                                  subs["questions"][k]["serialno"]=k+1
                                  k +=1
    #ss=json.dumps(json_temp)
    return json_temp

def getAnswer(qid):
    qid=int(qid)
    if qid in range(e1_start,e1_end):
        e1_readjson=json.loads(open(os.path.join(APP_STATIC_JSON, 'E1-Reading.json')).read())
        for psg in e1_readjson["passageArray"]:
            for key in psg["questions"]:
                if int(key["id"]) == qid:
                    for op in key["options"]:
                        if op[0] == "=":
                            return op[1:len(op)]
    if qid in range(e2_start,e2_end):
        e2_lsnjson=json.loads(open(os.path.join(APP_STATIC_JSON, 'E2-Listening.json')).read())
        for key in e2_lsnjson["videoArray"]:
            for qn in key["questions"]:
                if int(qn["id"]) == qid:
                    for op in qn["options"]:
                        if op[0] == "=":
                            return op[1:len(op)]

def admin_login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs): 
        user = session['user'] if 'user' in session else None
        if not user:
            return render_template('login.html')
        if 'role' not in session['user']:
            return render_template('unauthorized.html')
        if session['user']['role'] != 'admin':
            return render_template('unauthorized.html')
        return func(*args, **kwargs)
    return decorated_function

def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs): 
        user = session['user'] if 'user' in session else None
        if not user:
            return render_template('login.html')
        if 'role' not in session['user']:
            return render_template('unauthorized.html')
        return func(*args, **kwargs)
    return decorated_function

@app.route('/test')
def test():
    app.logger.debug('in testing')
    app.logger.info('in testing1')

    return "sent"

@app.route("/testmail")
def testmail():
   msg = Message('Hello', sender = 'RGUKT QUIZ <rguktemailtest@gmail.com>', recipients = ['sirimala.sreenath@gmail.com'])
   msg.body = "Hello Flask message sent from Flask-Mail"
   mail.send(msg)
   return "Sent"

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/javascripts/<path:path>')
def send_javascripts(path):
    app.logger.info("seeking for "+path)
    return send_from_directory('static/javascripts', path)

@app.route('/video/<path:path>')
def send_video(path):
    return send_from_directory('static/video', path)

@app.route('/stylesheets/<path:path>')
def send_stylesheets(path):
    return send_from_directory('static/stylesheets', path)

@app.route('/checklogin')
def checklogin():
    myname = "Veda"
    emailaddr = "vy@fju.us"
    ss = Response.query.filter_by(emailid=emailaddr).first()
    if ss is None:
        response = Response(emailid=emailaddr, name=myname)
        db.session.add(response)
        db.session.commit()
    sp=userDetails.query.filter_by(email=emailaddr).first()
    if sp is not None:
        return render_template('quiz.html')
    else:
        return render_template('register.html')

@app.route('/savepersonaldata', methods=['POST'])
def savepersonaldata():
    userdetails = userDetails(name=request.form['name'],email="vy@fju.us",phno=request.form['phone'],rollno=request.form['rollno'],learningcenter=request.form['learningcenter'])
    db.session.add(userdetails)
    db.session.commit()
    return redirect(url_for('startquiz'))

@app.route('/getquizstatus', methods=['POST'])
def getquizstatus():
    #qbank=QuestionBank()
    # check if candidate is resuming the test
    r1 = Randomize.query.filter_by(user1="vy@fju.us").all()
    #print r1
    #logging.error("random values")
    if r1:
        isRandomized = True
        qid_list={}
        for data in r1:
            qid_list[int(data.qno)] = data.serialno
        json_data=getQuestionPaper(qid_list)
    else:
        isRandomized = False
        json_data=generateQuestionPaper()
    # print json_data;
    # TODO
    # New json_data returned from the question bank if is randomized is false
    # Else list of question ID should be fetched from randomize table
    # pass the question IDs list to the question bank to get json_data

    #json_data = json.loads(open(os.path.join(APP_STATIC_JSON,'quizdata.json')).read())
    for key in json_data:
        if  key == "section":
            section = json_data[key]
            for s in  section:
                for key in s:
                    if key == "subsection":
                        for subs in s[key]:
                            for key in subs:
                                if key == "questions":
                                    for q in subs[key]:
                                        if not isRandomized:
                                            r = Randomize(user1 = "vy@fju.us", serialno = q['serialno'], qno=q["id"])
                                            db.session.add(r)
                                            db.session.commit()
                                        else:
                                            #print q['id']
                                            #logging.error("question id is:")
                                            r = Randomize.query.filter_by(user1 = "vy@fju.us", qno = q["id"]).all()
                                        q1 = Response.query.filter_by(emailid="vy@fju.us", currentQuestion=q["id"]).order_by(Response.time.desc()).first()
                                        if q1:
                                            q["responseAnswer"]=q1.submittedans
                                            q["responseTime"]=q1.responsetime
                                            q["status"]=q1.q_status

    td = TestDetails.query.filter_by(email="vy@fju.us").first()
    if td:
        if td.testend:
            json_data['quizStatus'] = 'END'
        else:
            json_data['quizStatus'] = 'INPROGRESS'
    else:
        json_data['quizStatus'] = 'START'

    ss=json.dumps(json_data)
    return ss
requests
@app.route('/testtime', methods=['POST'])
def testtime():
    duration = 60 * 60
    td = TestDetails.query.filter_by(email="vy@fju.us").first()
    if td is None:
        testdetails = TestDetails(email="vy@fju.us",test=True,delays=0.0)
        db.session.add(testdetails)
        db.session.commit()
        obj = {u"timeSpent":0, u"timeRemaining":duration, u"quizStatus": u"INPROGRESS"}
    else:
        if not td.testend:
            currTime = datetime.now()
            deltaTime = (currTime - td.lastPing).total_seconds()
            if(deltaTime > 65.0):
                td.delays = td.delays + deltaTime - 60.0
                db.session.add(td)
                db.session.commit()
            timeSpent = (currTime - td.teststime).total_seconds() - td.delays

            if timeSpent >= duration:
                td.testend = True
                quizStatus = u"END"
            else:
                quizStatus = u"INPROGRESS"
            obj = {u"timeSpent" : timeSpent, u"quizStatus": quizStatus, u"timeRemaining" : duration - timeSpent}
            td.lastPing = currTime
            db.session.add(td)
            db.session.commit()
        else:
            obj = {u"quizStatus":u"END"}
    ss=json.dumps(obj)
    return ss

@app.route('/submitanswer', methods=["POST"])
def submitanswer():
    td=TestDetails.query.filter_by(email="vy@fju.us").first()
    if td and not td.testend:
        validresponse="false"
        status=""
        errortype=""
        q_status=""
        score=0
        type=""
        vals = json.loads(cgi.escape(request.get_data()))
        vals = vals['jsonData']
        currentQuestion =vals['id']
        submittedans = vals['responseAnswer']
        responsetime = vals['responseTime']
        # opening  json file of quizdata
        #logging.error(currentQuestion,submittedans)
        currentQuestion=int(currentQuestion)
        if submittedans == "skip":
            validresponse="true"
            q_status="skip"
        
        elif currentQuestion in range(e3_start,e3_end):
            r=UserAudio.query.filter_by(user="vy@fju.us").first()
            if r :
                q_status="submitted"
                status="success"
                validresponse="true"
            else :
                q_status="submitted"
                status="success"
                validresponse="true"
        elif currentQuestion in range(e4_start,e4_end):
            q_status="submitted"
            status="success"
            validresponse="true"
        else :
            q_status="submitted"
            status="success"
            validresponse="true"
            cans=getAnswer(currentQuestion)
            if cans == submittedans:
                score = 1
        if validresponse=="true":
            status="success"
            if q_status!="skip":
                q_status="submitted"
        else:
            status="error"

        # creating json file for error response
        # placing in to the database
        n1=int(currentQuestion)
        data=Response(serialno=n1,emailid="vy@fju.us",name="Veda",currentQuestion=str(currentQuestion),submittedans=submittedans,responsetime=responsetime,q_status=q_status,q_score=score)
        db.session.add(data)
        db.session.commit()

        # added time taken based on the timer
        obj = {u"status":status , u"q_status":q_status, u"validresponse":validresponse, u"qid":currentQuestion}

    else:
        obj = {u"testEnd" : True}
    ss=json.dumps(obj)
    return ss

@app.route('/getResult', methods=["GET"])
def getResult():
    totalscore = 0
    q1= Response.query.filter_by(emailid="vy@fju.us").order_by(Response.serialno, Response.time.desc()).all()
    questionresponses_dict = {}
    question_records=[]
    totalscore=0
    s1="0"
    for q in q1:
        if q.responsetime is not None:
            if q.currentQuestion != s1 :
                s1=q.currentQuestion
                #totalscore=q.responsetime+q.q_score
                question = {"user":"Veda","submittedans":q.submittedans, "q_score":q.q_score,"currentQuestion":s1,"responsetime":q.responsetime}
                question_records.append(question)
    questionresponses_dict["question"]=question_records
    questionresponses_dict["totalscore"]=totalscore
    ss=json.dumps(questionresponses_dict)
    return ss

@app.route('/getScore', methods=["GET"])
def getScore():
    score=0
    q1= Response.query.filter_by(emailid="vy@fju.us").all()
    for q in q1:
        score=score+1
    template_values = {
        'p': q1,
        'score1':score,
        }
    return render_template("testresult.html")

@app.route('/autosaveEssay', methods=["POST"])
def autosaveEssay():
    vals = json.loads(cgi.escape(request.get_data()))
    vals = vals['jsonData']
    qid = vals['currentQuestion']
    print(vals)
    ans = vals['draft']
    qattemptedtime = vals['responsetime']
    print(vals)
    data1 = EssayTypeResponse.query.filter_by(useremailid = "vy@fju.us", qid = qid).first()
    print(qid)

    if data1:
        data1.qattemptedtime=qattemptedtime
        data1.ansText = ans
        db.session.add(data1)
        db.session.commit()

    else:
        data = EssayTypeResponse(useremailid="vy@fju.us", qid=qid, qattemptedtime=qattemptedtime, ansText = ans)
        db.session.add(data)
        db.session.commit()

    ss=json.dumps(vals)
    return ss

@app.route('/uploadredirect', methods=["POST"])
def uploadredirect():
    return redirect(url_for("/upload_audio"))

@app.route('/upload_audio', methods=["POST"])
def upload_audio():
    try:
        files = request.files.getlist('file')
        if files:
            useraudio = UserAudio(user="vy@fju.us", blob1=files[0].file.read())
            db.session.add(useraudio)
            db.session.commit()
    except Exception as e:
        return "Record Not Saved.\n\n"+str(e)

@app.route('/view_audio/<link>', methods=["GET"])
def view_audio(link):
    event = UserAudio.query.get_or_404(link)
    return app.response_class(event.blob1, mimetype='application/octet-stream')

# @app.route('/audio')
# def audio():

@app.route('/endtest', methods=["POST"])
def endtest():
    val = json.loads(cgi.escape(request.get_data()))
    val = val['jsonData']
    print(val)
    testend = val['testend']
    score = val['finalScore']
    spklink = val['spklink']
    print(testend)
    data1 = TestDetails.query.filter_by(email = "vy@fju.us").first()
    userdata=userDetails.query.filter_by(email = "vy@fju.us").first()
    learningcenter=userdata.learningcenter    
    if data1:
        data1.testend = testend
        data1.score = score
        data1.learningcenter = learningcenter
        db.session.add(data1)
        db.session.commit()

@app.route('/startquiz')
def startquiz():
    return render_template('quiz.html')

def generate_unique_code():
    return str(uuid.uuid1()).replace("-", "")


def valid_user_login(email, password):
    user = Users.query.filter_by(emailid=email, password=hashlib.md5(password.encode('utf-8')).hexdigest()).first()
    if user:
        return user
    return None

@app.route('/student', methods=['GET'])
@login_required
def student():
    if request.method == "GET":
        return render_template('student.html')

@app.route('/studenttests', methods=['GET'])
@login_required
def studenttests():
    emailid = session["user"]['email']
    result = StudentTests.query.filter_by(emailid=emailid).first()
    final = {"data": []}
    if result != None:
        tests = result.getTests()
        for name in tests:
            result = Tests.query.filter_by(name=name).first()
            tests = str(result).split("::")
            if result.isHosted():
                button = "<a href='#' class='btn btn-sm btn-primary'>Attempt Test</a>"
            else:
                button = "<a href='#' class='btn btn-sm btn-warning' disabled>Locked</a>"
            tests.append(button)
            final["data"].append(tests)
    return json.dumps(final)

@app.route('/verify/<email>/<code>', methods=['GET'])
def verify_unique_code(email, code):
    if request.method == 'GET':
        email = base64.b64decode(email).decode()
        app.logger.info(email)
        app.logger.info(code)

        user = Users.query.filter_by(emailid=email, password=code).first()
        if user:
            try:
                user.verified = True
                db.session.add(user)
                db.session.commit()
                session['user'] = {}
                session['user']['email'] = user.emailid
                session['user']['permissions'] = []
                session['user']['allow_to_set_password'] = True
                return render_template("set_password.html",
                    success="You are successfully activated your account.\n Please login")
            except Exception as e:
                return render_template("error.html", error=e)
        return render_template("unauthorized.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    app.logger.info('Login page accessed')

    # Create default admin credentials if not already exists
    admin = Users.query.filter_by(user_type="admin").first()
    if admin is None:
        password = hashlib.md5("admin".encode('utf-8')).hexdigest()
        row = Users("admin@quiz.in",password,"admin",True)
        db.session.add(row)
        db.session.commit()

    if 'user' in session:
        if 'role' in session['user']:
            return redirect(url_for(session['user']['role']))

    if request.method == "GET":
        return render_template('login.html')

    if request.method == "POST":
        app.logger.info('Login page post request')

        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

        email = request.form['email']
        password = request.form['password']
        user = valid_user_login(email, password)

        if user:
            if user.verified != "false":
                email = user.emailid
                role = user.user_type
                session['user'] = {}
                session['user']['email'] = email
                session['user']['role'] = role
                session['user']['permissions'] = permissions_object[role]
                session['user']['allow_to_set_password'] = True

                message = "You are logged in as %s" % email
                logging.debug(user.verified)
                login_log.debug("Logged in as %s with IP %s" % (email, ip_address))
                return redirect(url_for(role))
            else:
                logging.debug("Here is one thing working")

                error = "Please activate your account, using the link we sent to your registered email"
                login_log.debug("Tried to login in as %s from IP %s, but Account not activated." % (email, ip_address))

        else:
            error = "Invalid Credentials"
            
            login_log.debug("Tried to login in as %s from IP %s, but Invalid Credentials." % (email, ip_address))
        return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    if 'user' not in session:
        return redirect(url_for('login'))

    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    login_log.debug("%s logged out with IP %s." % (session['user']["email"], ip_address))
    
    session.pop('user', None)
    return redirect(url_for('login'))

def sendMail(encode='Testing', code='Testing', email='rguktemailtest@gmail.com'):
    app.logger.debug("send mail function")
    body = """Dear Student,<br> This email message is sent by the online quiz portal. 
    By clicking the link below you are verifying that this email belongs to you and your account will be actiavted. 
    Click on the link below and follow the instructions to complete the registration process. 
    <a href=%s/verify/%s/%s>Verify</a> """ % (request.host, encode, code)
    response = requests.post(
        "https://api.mailgun.net/v3/rguktrkv.ac.in/messages",
        auth=("api", os.environ['YOUR_MAIL_GUN_KEY']),
        data={"from": "RGUKT QUIZ <news@rguktrkv.ac.in>",
              "to": [email],
              "subject": 'Account Verification for RGUKT QUIZ',
              "text": '',
              "html": body})
    app.logger.info([response.status_code, response.text])
    if response.status_code == 200:
        return True
    else:
        return False


# def sendMail(encode='', code='', email='rguktemailtest@gmail.com'):
#     app.logger.debug("send mail function")
#     msg = Message('Account Verification for RGUKT QUIZ', sender = 'RGUKT QUIZ <rguktemailtest@gmail.com>', recipients = [email])
#     msg.html = """Hi Receipient,\n Please click on link given below to activate your account. 
#     <a href=%s/verify/%s/%s """ % (request.host, encode, code)
#     mail.send(msg)
#     return True

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if 'user' in session:
        return redirect(url_for(session['user']['role']))
    if request.method == "GET":
        login_log.debug("Get registration Form")
        return render_template('registration.html')
    elif request.method == "POST":
        login_log.debug("post registration Form")

        message = ""
        message_staus = ""
        try:
            login_log.debug("post registration Form")

            email = request.form["email"]
            exists = db.session.query(Users).filter_by(emailid=email).scalar() is not None
            # if email[-9:] != ".rgukt.in":
            #     message = "Email ID must be from RGUKT"
            #     message_staus = "danger"

            if not exists:
                code = generate_unique_code()
                user = Users(email, code,"student",False)
                db.session.add(user)
                db.session.commit()
                encode = base64.b64encode(email.encode()).decode()
                
                sent = sendMail(encode, code, email)
                if sent:
                    app.logger.debug("an email has been sent to your email address "+email+". Please go to your inbox and click on the link to verify and activate your account")
                    message = "an email has been sent to your email address "+email+". Please go to your inbox and click on the link to verify and activate your account"
                    message_staus = "success"
                else:
                    db.session.delete(user)
                    db.session.commit()
                    app.logger.debug("Something went wrong in sending verification mail, please try again")
                    message = "Something went wrong in sending verification mail, please try again"
                    message_staus = "danger"
            else:
                message = str(email) + " already exists, Please contact admin"
                message_staus = "danger"

        except Exception as e:
            db.session.rollback()
            message = e
            message_staus = "danger"
            app.logger.debug("Something went wrong in sending verification mail, please try again "+str(e))
            

        return render_template('registration.html', message=message, status=message_staus)

@app.route('/setpassword', methods=['GET', 'POST'])
def setpassword():
    if 'user' not in session:
        return redirect(url_for("login"))
    if 'allow_to_set_password' not in session['user']:
        print(session['user'])
        return redirect(url_for("login"))
    if request.method == "GET":
        return render_template('set_password.html')
    elif request.method == "POST":
        email = session["user"]['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            user = Users.query.filter_by(emailid=email).first()
            if user:
                user.password = hashlib.md5(password.encode('utf-8')).hexdigest()
                db.session.add(user)
                db.session.commit()
                message = "Password successfully change, Please login"
                return render_template('login.html', success=message)
            else:
                message = "Your email address dosen't exist, Please register"
                message_staus = "error"
                return render_template("registration.html", message=message, status=message_staus)

        else:
            message = "Password and ConfirmPassword should match"
            message_staus = "error"

            return render_template("set_password.html", message=message, status=message_staus)


#==================================================== ADMIN PAGE =====================================================
# def valid_admin_login(email, password):
#     result = AdminDetails.query.filter_by(email=email).first()
#     if str(result) == str(password):
#         return True
#     return False

# @app.route('/adminlogin', methods=['GET', 'POST'])
# def adminlogin():
#     ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    
#     if db.session.query(AdminDetails).first() is None:
#         row = AdminDetails("admin@quiz.in","admin")
#         db.session.add(row)
#         db.session.commit()

#         login_log.debug("Created Default Admin Credentials.")
    
#     message = None
#     error = None
    
#     if request.method == "POST":
#         email = request.form['email']
#         password = request.form['password']
        
#         if valid_admin_login(email,password):
#             session['adminemail'] = email
#             message = "You are logged in as %s" % email
            
#             login_log.debug("Logged in as %s with IP %s" % (email, ip_address))
#             return redirect(url_for('admin'))
#         else:
#             error = "Invalid Credentials"
            
#             login_log.debug("Tried to login in as %s from IP %s, but Invalid Credentials." % (email, ip_address))
#             return render_template('login.html', error=error)
    
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
#     login_log.debug("%s logged out with IP %s." % (session["user"]['email'], ip_address))
    
#     session.pop('adminemail', None)
#     return redirect(url_for('adminlogin'))

@app.route('/admin')
@admin_login_required
def admin():
    return render_template('admin.html')    
    
    # if 'adminemail' in session:
    #     return render_template('admin.html')    
    # return redirect(url_for('adminlogin'))

def checkStudentTests(emailid):
    return StudentTests.query.filter(StudentTests.emailid == emailid).first()

def validate_name(name):
    result = Tests.query.filter_by(name=name).first()
    return result == None

def validate_date(date):
    today = datetime.now()
    return datetime.strptime(date, '%d/%m/%Y') > today

def validate_file(file_name,data):
    file_report = {}
    file_report["name"] = file_name
    if file_name != '' and allowed_file(file_name):
        if file_name == "QP_template.json":
            if not validate_qp_template.validate(data):
                file_report["isValid"] = validate_qp_template.errors
            else:
                file_report["isValid"] = True
        else:
            if schema_type_mapping[data["types"]].validate(data):
                file_report["isValid"] = True
            else:
                file_report["isValid"] = schema_type_mapping[data["types"]].errors
    else:
        file_report["isValid"] = 'Invalid Filename or Extension.'
    return file_report

def save_file(folder_name,file_name,data):
    filename = secure_filename(file_name)
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name+"/")
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w+") as f:
        fJson.dump(data, f)
    # file.save(os.path.join(path, filename))
    # file.close()

@app.route('/create', methods=["GET","POST"])
@admin_login_required
def create():
    admin = session["user"]['email']

    if request.method == "GET":
        session["message"] = {}
        app.logger.info('Create Test Page accessed by %s' %admin)
        return render_template("create.html")

    if request.method=="POST":
        test_name = request.form['name']
        nameValid = validate_name(test_name)

        hosting_date = request.form['datepicker']
        dateValid = validate_date(hosting_date)

        testValid = False
        if nameValid and dateValid:
            test = Tests(test_name, session["user"]['email'], hosting_date)
            db.session.add(test)
            db.session.commit()
            testValid = True
            app.logger.info('%s created a Test - %s' %(admin,test_name))
            session["TestID"] = test_name
            session["hosting_date"] = hosting_date
            return redirect(url_for("addstudents"))
        else:
            session["message"] = {"Valid Name":nameValid, "Valid Date":dateValid, "Valid Test":testValid}
            app.logger.info('Failed to create Test - %s' %test_name)
            return render_template("create.html")

def loadTestSet():
    student = Users.query.filter_by(user_type="student").first()
    if student is None:
        for num in range(20):
            row = Users("student"+str(num)+"@quiz.in","student","student",True)
            db.session.add(row)
            db.session.commit()

def isRegistered(studentemail):
    registered = Users.query.filter(Users.emailid == studentemail).first() != None
    return registered

# def Invited(studentemail,testid):
#     studentrow = StudentTests.query.filter(StudentTests.emailid == studentemail).first()
#     if studentrow != None:
#         return testid in studentrow.getTests()
#     return False

@app.route('/addstudents', methods=["GET", "POST"])
@admin_login_required
def addstudents():
    testID = session["TestID"]
    hosting_date = session["hosting_date"]

    app.logger.info('Add Students Page (%s) accessed by %s' %(testID,admin))

    # Create sample sudents for testing
    loadTestSet()
    
    if request.method == "GET":
        session['students'] = []
        return render_template("add_students.html")
    
    if request.method == "POST":
        session["students"] = []
        try:
            students_list = request.form["studentslist"].split(", ")
            for student in students_list:
                if student == "":
                    continue
                if isRegistered(student):
                    qry = StudentTests.query.filter(StudentTests.emailid == student).first()
                    if qry != None:
                        if testID in qry.testslist:
                            session["students"].append(student+" is already Invited.")
                        else:
                            qry.testslist.append(testID)
                            db.session.commit()
                    else:
                        tests = [testID]
                        studenttests = StudentTests(student,tests)
                        db.session.add(studenttests)
                        db.session.commit()
                        session["students"].append(student+" is Invited.")
                        app.logger.info('%s is Invited' %student)
                else:
                    session["students"].append(student+" is not Registered.")
                    app.logger.info('%s is not registered' %student)
        except Exception as e:
            session["students"].append(e)

        app.logger.info('%s added %s to %s' %(admin,session["students"],testID))
        return render_template("add_students.html")

@app.route('/loadtests', methods=["GET"])
@admin_login_required
def loadtests():
    creator = session["user"]['email']
    app.logger.info("Getting all tests created by " + creator)
    result = Tests.query.filter_by(creator=creator).all()
    final = {}
    final["data"] = []
    for test in result:
        test = str(test).split("::")
        button = "<a href='#' class='btn btn-sm btn-primary' disabled>Preview Test</a>"
        test.append(button)
        final["data"].append(test)
    return json.dumps(final)

@app.route('/autocomplete', methods=['GET'])
@admin_login_required
def autocomplete():
    search = request.args.get('q')
    query = db.session.query(Users.emailid).filter(Users.emailid.like('%' + str(search) + '%'))
    results = [mv[0] for mv in query.all()]
    return jsonify(matching_results=results)
