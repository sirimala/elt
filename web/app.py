from flask import Flask, flash, redirect, render_template, \
     request, jsonify, url_for, session, send_from_directory, \
     make_response, Response as ress
from flask_sqlalchemy import SQLAlchemy
from cerberus import Validator
from sqlalchemy import cast, func, distinct
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSON
from functools import wraps
from datetime import datetime, timedelta
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
from flask_csv import send_csv
import pytz
import io
import csv
import inspect

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

e1_start=1;e1_end=100;e2_start=101;e2_end=200;e3_start=201;e3_end=300;
e4_start=301;e4_end=400;

#create a local timezone (Indian Standard Time)
IST = pytz.timezone('Asia/Kolkata')

global status
global errortype

@app.errorhandler
def default_error_handler(error):
    '''Default error handler'''
    return {'message': str(error)}, getattr(error, 'code', 500)

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
    email = db.Column(db.String(180), unique=True)
    password = db.Column(db.String(1000))

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
    start_date = db.Column(db.String(80))
    end_date = db.Column(db.String(80))
    # json = db.Column(db.String(1000))
    creator = db.Column(db.String(180))
    time = db.Column(db.DateTime(), default=pytz.utc.localize(datetime.utcnow()), onupdate=pytz.utc.localize(datetime.utcnow()))

    def __init__(self, name, creator, start_date, end_date):
        self.name = name
        self.creator = creator
        self.start_date = start_date
        self.end_date = end_date
        self.time = pytz.utc.localize(datetime.utcnow())
        # self.json = json
    def isHosted(self):
        today = datetime.now(IST)
        start_date = datetime.strptime(self.start_date, '%d-%m-%Y %H:%M')
        end_date = datetime.strptime(self.end_date, '%d-%m-%Y %H:%M')

        return IST.localize(start_date) < today < IST.localize(end_date)

    def __repr__(self):
        return str(self.name)+"::"+str(self.start_date)+"::"+str(self.end_date)

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

class TestAudio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blob1 = db.Column(db.LargeBinary)

    def __init__(self, blob1):
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
    teststime=db.Column(db.DateTime(), default=datetime.utcnow)
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
    testctime = db.Column(db.DateTime(), default=datetime.utcnow)
    submittedans = db.Column(db.Text)
    responsetime = db.Column(db.Float)
    q_score = db.Column(db.Integer)
    q_status = db.Column(db.String(120))
    time = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow )
    currentQuestion=db.Column(db.String(120))
    serialno=db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(Response, self).__init__(**kwargs)

    # def __repr__(self):
    #     return str({
    #                 "id":self.id,
    #                 "name": self.name,
    #                 "emailid": self.emailid,
    #                 "pin": self.pin,
    #                 "testctime": self.testctime,
    #                 "submittedans": self.submittedans,
    #                 "responsetime": self.responsetime,
    #                 "q_score": self.q_score,
    #                 "q_status": self.q_status,
    #                 "time": self.time,
    #                 "currentQuestion": self.currentQuestion,
    #                 "serialno": self.serialno
    #                 })
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
        if qid in list(range(e1_start,e1_end)):
              e1_readjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E1-Reading.json')).read())
              for key in e1_readjson["passageArray"]:
                    for qn in key["questions"]:
                          pid=qn["id"]
                          if int(pid) == qid:
                                json_temp["section"][2]["subsection"][0]["passage"]=key["passage"]
                                json_temp["section"][2]["subsection"][0]["questions"].append(qn)
                                json_temp["section"][2]["subsection"][0]["questions"][m]["serialno"] = qid_list[qid]
                                m +=1
        if qid in list(range(e2_start,e2_end)):
              e2_lsnjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E2-Listening.json')).read())
              for key in e2_lsnjson["videoArray"]:
                    for qn in key["questions"]:
                          pid=qn["id"]
                          if int(pid) == qid:
                                json_temp["section"][0]["subsection"][0]["link"]=key["link"]
                                json_temp["section"][0]["subsection"][0]["questions"].append(qn)
                                json_temp["section"][0]["subsection"][0]["questions"][n]["serialno"] = qid_list[qid]
                                n +=1
        if qid in list(range(e3_start,e3_end)):
              e3_spkjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E3-Speaking.json')).read())
              for key in e3_spkjson["questions"]:
                    if int(key["id"]) == qid:
                          json_temp["section"][1]["subsection"][0]["questions"].append(key)
                          json_temp["section"][1]["subsection"][0]["questions"][p]["serialno"] = qid_list[qid]
                          p += 1
        if qid in list(range(e4_start,e4_end)):
              e4_wrtjson=json.loads(open(os.path.join(APP_STATIC_JSON,'E4-Writing.json')).read())
              for key in e4_wrtjson["questions"]:
                    if int(key["id"]) == qid:
                          json_temp["section"][3]["subsection"][0]["questions"].append(key)
                          json_temp["section"][3]["subsection"][0]["questions"][q]["serialno"] = qid_list[qid]
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
                                serialno=list(range(0,len(video_list)))
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
                                serialno=list(range(0,len(qns_list)))
                                shuffle(serialno)
                                for no in list(range(0,cnt)):
                                    subs["questions"].append(qns_list[serialno[no]])
                                    subs["questions"][no]["serialno"]=no+1
                            if types == "passage":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                psglist=json_subs["passageArray"]
                                serialno=list(range(0,len(psglist)))
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
                                serialno=list(range(0,len(qns_list)))
                                shuffle(serialno)
                                for no in list(range(0,cnt)):
                                    subs["questions"].append(qns_list[serialno[no]])
                                    subs["questions"][no]["serialno"]=no+1
                            if name == "T2-Listening":
                                #print name
                                json_subs=json.loads(open(os.path.join(APP_STATIC_JSON,name+".json")).read())
                                video_list=json_subs["videoArray"]
                                serialno=list(range(0,len(video_list)))
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

    if qid in list(range(e1_start,e1_end)):
        e1_readjson=json.loads(open(os.path.join(APP_STATIC_JSON, 'E1-Reading.json')).read())
        for psg in e1_readjson["passageArray"]:
            for key in psg["questions"]:
                if int(key["id"]) == qid:
                    for op in key["options"]:
                        if op[0] == "=":
                            return op[1:len(op)]
    if qid in list(range(e2_start,e2_end)):
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

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        app.logger.info('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            app.logger.info('{}{}'.format(subindent, f))

@app.before_request
def before_request():
    db.session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)
    db.session.modified = True
    app.logger.info(["Session expire time extentended to ", datetime.now(IST) + app.permanent_session_lifetime])

@app.route('/error/<error>')
def error(error):
    return render_template('error.html', error=error)

@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        app.logger.debug('in testing')
        # files = request.files.getlist('file')
        data = request.files['file'].read()
        # data = files[0].file.read()
        # app.logger.info(data)
        test = TestAudio(data)
        db.session.add(test)
        db.session.commit()
        # test = TestAudio.query.first()
        # app.logger.info([type(test.blob1), dir(test.blob1)])
        # return test.blob1
        return app.response_class(base64.b64encode(test.blob1), mimetype="audio/webm")
        # return app.response_class(test.blob1, mimetype='application/octet-stream')
    else:
        return str(datetime.now())
        return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="/test" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

def store_audio(user, blob):
    try:
        useraudio = UserAudio(user=user, blob1=blob)
        db.session.add(useraudio)
        db.session.commit()
        return useraudio.blob1
    except Exception as e:
        app.logger.error(e)
        return None

@app.route('/audio_upload', methods=["POST"])
@login_required
def audio_upload():
    file = request.files['file']
    user=session['user']['email']
    if file:
        useraudio = store_audio(user, file.read())
        if useraudio:
            return app.response_class(base64.b64encode(useraudio), mimetype="audio/webm")
        else:
            return "Record Not Saved.\n\n"+str(useraudio)
    else:
        return "Audio not recieved from user."


@app.route('/get_audio', methods=["GET"])
@login_required
def get_audio(user=None):
    app.logger.info("get audio called")
    user = user if user else session['user']['email']
    event = UserAudio.query.filter_by(user=user).order_by(UserAudio.time.desc()).first()
    if not event:
        return "Audio not found"
    # app.logger.info(event.blob1)
    return app.response_class(base64.b64encode(event.blob1), mimetype="audio/webm")
    # return '<audio src="data:audio/webm;base64,'+base64.b64encode(event.blob1).decode('utf-8')+'" controls></audio>'


@app.route('/')
@login_required
def index(role=None):
    # return render_template('index.html')
    if not role:
        if 'role' not in session['user']:
            return "Your account still not activated, Please come here after activation of your account."
        role = session['user']['role']
    return redirect(url_for(role))


def get_role_from_session():
    if 'user' in session:
        if 'role' in session['user']:
            return session["user"]['role']
    return None

def get_email_from_session():
    if 'user' in session:
        return session["user"]['email']
    return None


def delete_entries(Object, email):
    try:
        entries = Object.query.filter_by(emailid=email).all()
    except Exception as e:
        app.logger.error(e)
        entries = Object.query.filter_by(email=email).all()
    for entry in entries:
        db.session.delete(entry)
    db.session.commit()

def allowed_to_take_test(testid="", email=None):

    email = email if email else session['user']['email']

    studenttests = getFirstTestRecord(email)
    if get_role_from_session()=="admin":
        delete_entries(Response(), email)
        delete_entries(TestDetails(), email)
        return True
    if not studenttests:
        app.logger.info(studenttests)
        return False
    app.logger.info(studenttests.testslist)
    if testid in studenttests.testslist:
        return True
    return False

@app.route('/quiz')
@login_required
def quiz(email=None):
    # return render_template('index.html')
    role = get_role_from_session()
    email = email if email else get_email_from_session()
    if not role:
        return "Your account still not activated, Please come here after activation of your account."
    if allowed_to_take_test("English Literacy Test", email):
        # return render_template('index.html')
        if len(TestDetails.query.filter_by(email=email).all()) != 0:
            return redirect("/checklogin")
        else:
            return render_template('index.html')
    app.logger.info("I am not admin")
    return redirect(url_for(role))

@app.route('/javascripts/<path:path>')
def send_javascripts(path):
    app.logger.info("seeking for "+path)
    return send_from_directory('static/javascripts', path)

@app.route('/src/<path:path>')
def send_src(path):
    app.logger.info("seeking for "+path)
    return send_from_directory('static/src', path)

@app.route('/js/<path:path>')
def send_js(path):
    app.logger.info("seeking for "+path)
    return send_from_directory('static/js', path)

@app.route('/video/<path:path>')
def send_video(path):
    return send_from_directory('static/video', path)

@app.route('/stylesheets/<path:path>')
def send_stylesheets(path):
    return send_from_directory('static/stylesheets', path)

def add_first_response(email):
    response = Response.query.filter_by(emailid=email).first()
    if response is None:
        try:
            response = Response(emailid=email, name=email)
            db.session.add(response)
            db.session.commit()
            return True
        except Exception as e:
            app.logger.error(e)
            return False
    return True

def get_user_details(email):
    return userDetails.query.filter_by(email=email).first()

@app.route('/checklogin')
@login_required
def checklogin(email=None):
    email = email if email else get_email_from_session()
    first_response = add_first_response(email)
    if not first_response:
        return redirect(url_for("error", error="checklogin: Something is wrong with checking your session. Please contact test admin."))
    
    userdetails = get_user_details(email)
    if userdetails:
        return redirect(url_for("startquiz"))
    else:
        return render_template('register.html')

def add_user_profile(name,email,phno,rollno,learningcenter):
    userdetails = userDetails.query.filter_by(email=email).first()
    if not userdetails:
        try:
            userdetails = userDetails(name=name,email=email,phno=phno,rollno=rollno,learningcenter=learningcenter)
            db.session.add(userdetails)
            db.session.commit()
            return True
        except Exception as e:
            app.logger.error(e)
            return False
    return False

@app.route('/savepersonaldata', methods=['POST'])
@login_required
def savepersonaldata(email=None):
    name = request.form['name']
    email = email if email else get_email_from_session()
    phno=request.form['phone']
    rollno=request.form['rollno']
    learningcenter=request.form['learningcenter']

    addprofile = add_user_profile(name,email,phno,rollno,learningcenter)
    if not addprofile:
        return redirect(url_for("error", error="savepersonaldata: Error updating your profile."))
    return redirect(url_for('startquiz'))

def checkrandomizetable(email):
    return Randomize.query.filter_by(user1=email).all()

def qidlisttodict(question_ids):
    qid_list={}
    for data in question_ids:
        qid_list[int(data.qno)] = data.serialno
    return qid_list

def add_to_randomize(email,serialno,qno):
    try:
        r = Randomize(user1 = email, serialno = serialno, qno=qno)
        db.session.add(r)
        db.session.commit()
    except Exception as e:
        app.logger.error(e)

def setquizstatus(email):
    td = TestDetails.query.filter_by(email=email).first()
    if td:
        if td.testend:
            return 'END'
        else:
            return 'INPROGRESS'
    else:
        return 'START'

def buildquizobject(email,isRandomized,json_data):
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
                                            add_to_randomize(email,q['serialno'], q["id"])
                                        #     r = Randomize.query.filter_by(user1 = session['user']['email'], qno = q["id"]).all()
                                        q1 = Response.query.filter_by(emailid=email, currentQuestion=q["id"]).order_by(Response.time.desc()).first()
                                        if q1:
                                            q["responseAnswer"]=q1.submittedans
                                            q["responseTime"]=q1.responsetime
                                            q["status"]=q1.q_status
    json_data['quizStatus'] = setquizstatus(email)
    return json_data
    

@app.route('/getquizstatus', methods=['POST'])
@login_required
def getquizstatus(email=None):
    email = email if email else get_email_from_session()

    question_ids = checkrandomizetable(email)
    
    # check if user resumes the test and get/generate accordingly
    if question_ids:
        isRandomized = True
        qid_dict = qidlisttodict(question_ids)
        json_data=getQuestionPaper(qid_dict)
        app.logger.info("User is Resuming Test")
    else:
        isRandomized = False
        json_data=generateQuestionPaper()
        app.logger.info("User is Starting Test")
    
    # build quiz object based on get/generated question paper and set
    quiz_status_object = buildquizobject(email,isRandomized,json_data)
    return json.dumps(quiz_status_object)

def addtestdetails(email,test,delays):
    try:
        testdetails = TestDetails(email=email,test=test,delays=delays)
        db.session.add(testdetails)
        db.session.commit()
        return True
    except Exception as e:
        app.logger.error(e)
        return False

def updatetimeobj(td):
    duration = 60*60
    if not td.testend:
        currTime = datetime.now()
        deltaTime = (currTime - td.lastPing).total_seconds()
        if(deltaTime > 65.0):
            td.delays = td.delays + deltaTime - 60.0
        
        timeSpent = (currTime - td.teststime).total_seconds() - td.delays

        if timeSpent >= duration:
            td.testend = True
            quizStatus = u"END"
        else:
            quizStatus = u"INPROGRESS"
        
        obj = {u"timeSpent" : timeSpent, u"quizStatus": quizStatus, u"timeRemaining" : duration - timeSpent}
        td.lastPing = currTime
    else:
        obj = {u"quizStatus":u"END"}

    return td, obj

@app.route('/testtime', methods=['POST'])
@login_required
def testtime(email=None):
    email = email if email else get_email_from_session()
    duration = 60 * 60

    td = TestDetails.query.filter_by(email=email).first()
    if td is None:
        addtestdetails(email,True,0.0)
        time_obj = {u"timeSpent":0, u"timeRemaining":duration, u"quizStatus": u"INPROGRESS"}
    else:
        td, time_obj = updatetimeobj(td)
        db.session.add(td)
        db.session.commit()
        
    return json.dumps(time_obj)

def getsubmittedresponse(email,request_data):
    vals = json.loads(cgi.escape(request_data))
    vals = vals['jsonData']

    currentQuestion =int(vals['id'])
    submittedans = vals['responseAnswer']
    responsetime = vals['responseTime']

    return email,currentQuestion,submittedans,responsetime

def storeresponse(email,currentQuestion,submittedans,responsetime,score=0):
    try:
        app.logger.info("Entered into Store Response %s %s %s %s" %(email,currentQuestion,submittedans,responsetime))
        if submittedans == "skip":
            validresponse="true"
            q_status="skip"
        
        elif currentQuestion in range(e3_start,e3_end):
            r=UserAudio.query.filter_by(user=email).first()
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

        data=Response(serialno=currentQuestion,emailid=email,name=email,currentQuestion=str(currentQuestion),submittedans=submittedans,responsetime=responsetime,q_status=q_status,q_score=score)
        db.session.add(data)
        db.session.commit()
        status="success"
    except Exception as e:
        app.logger.info(str(e))
        status="error"
    
    responseobj = {u"status":status , u"q_status":q_status, u"validresponse":"true", u"qid":currentQuestion}
    app.logger.info(responseobj)
    return responseobj

@app.route('/submitanswer', methods=["POST"])
@login_required
def submitanswer(email=None):
    email = email if email else get_email_from_session()

    td=TestDetails.query.filter_by(email=email).first()
    if td and not td.testend:
        request_data = str(request.get_data(),'utf-8')
        email, currentQuestion, submittedans, responsetime = getsubmittedresponse(email,request_data)
        responseobj = storeresponse(email, currentQuestion, submittedans, responsetime)        
    else:
        responseobj = {u"testEnd" : True}

    return json.dumps(responseobj)

def getResultOfStudent(email):
    totalscore = 0
    q1= Response.query.filter_by(emailid=email).order_by(Response.serialno, Response.time.desc()).all()
    questionresponses_dict = {}
    question_records=[]
    totalscore=0
    s1="0"
    for q in q1:
        if q.responsetime is not None:
            if q.currentQuestion != s1 :
                s1=q.currentQuestion
                #totalscore=q.responsetime+q.q_score
                question = {"user":session['user']['email'],"submittedans":q.submittedans, "q_score":q.q_score,"currentQuestion":s1,"responsetime":q.responsetime}
                question_records.append(question)
    questionresponses_dict["question"]=question_records
    questionresponses_dict["totalscore"]=totalscore
    ss=json.dumps(questionresponses_dict)
    return ss

@app.route('/getResult', methods=["GET", "POST"])
@login_required
def getResult():
    app.logger.info("Im in get result")
    if request.method=="POST":
        email = request.form['emailid']
        return getResultOfStudent(email)
        app.logger.info(["post", email])

    if request.method == "GET":
        email = session["user"]['email']
        return getResultOfStudent(email)


@app.route('/getstudentscore/<email>', methods=["GET"])
@admin_login_required
def getstudentscore(email):
    return render_template('studentscore.html', email=email)

@app.route('/viewresults', methods=["GET"])
@admin_login_required
def viewresults():
    return render_template("testresult.html")

@app.route('/getScore', methods=["GET"])
@admin_login_required
def getScore(email=None):
    if not email:
        email = session["user"]['email']
    score=0
    q1= Response.query.filter_by(emailid=email).all()
    for q in q1:
        score=score+1
    template_values = {
        'p': q1,
        'score1':score,
        }
    return render_template("testresult.html")

def getessayresponse(data):
    vals = json.loads(data.decode("utf-8"))
    vals = vals['jsonData']
    qid = vals['currentQuestion']
    ans = vals['draft'] if 'draft' in vals else ""
    qattemptedtime = vals['responsetime']
    return vals, qid, ans, qattemptedtime

def saveessay(row,email,qid,ansText,qattemptedtime):
    try:
        if row:
            row.qattemptedtime=qattemptedtime
            row.ansText = ans
            db.session.add(row)
            db.session.commit()
        else:
            data = EssayTypeResponse(useremailid=email, qid=qid, qattemptedtime=qattemptedtime, ansText = ans)
            db.session.add(data)
            db.session.commit()
        return True
    except Exception as e:
        app.logger.info(e)
        return False

@app.route('/autosaveEssay', methods=["POST"])
@login_required
def autosaveEssay(email=None):
    email = email if email else get_email_from_session()
    
    data = request.get_data()
    essay_response, qid, ans, qattemptedtime = getessayresponse(data)

    data = EssayTypeResponse.query.filter_by(useremailid = email, qid = qid).first()
    saveessay(data,email,qid,ans,qattemptedtime)
    
    return json.dumps(essay_response)

@app.route('/uploadredirect', methods=["POST"])
def uploadredirect():
    return redirect(url_for("/upload_audio"))

@app.route('/upload_audio', methods=["POST"])
@login_required
def upload_audio():
    try:
        files = request.files.getlist('file')
        if files:
            useraudio = UserAudio(user=session['user']['email'], blob1=files[0].file.read())
            db.session.add(useraudio)
            db.session.commit()
    except Exception as e:
        return "Record Not Saved.\n\n"+str(e)

@app.route('/view_audio/<link>', methods=["GET"])
@login_required
def view_audio(link):
    event = UserAudio.query.get_or_404(link)
    return app.response_class(event.blob1, mimetype='application/octet-stream')

# @app.route('/audio')
# def audio():
def getendtestdata(request_data):
    try:
        val = request_data['jsonData']
        testend = val['testend']
        score = val['finalScore']
        spklink = val['spklink']
    except Exception as e:
        app.logger.info(e)
        return False
    return val, testend, score, spklink

def getlearningcentre(email):
    try:
        userdata=userDetails.query.filter_by(email = email).first()
        learningcenter=userdata.learningcenter
        return learningcenter
    except Exception as e:
        app.logger.info(e)
        return False

def updatetestdetails(data,testend,score,learningcenter):
    try:
        data.testend = testend
        data.score = score
        data.learningcenter = learningcenter
        db.session.add(data)
        db.session.commit()
        return True
    except Exception as e:
        app.logger.info(e)
        return False

def updatelearningcentre(email):
    userdata = userDetails.query.filter_by(email=email).first()
    if userdata:
        return userdata.learningcenter
    return ""

@app.route('/endtest', methods=["POST"])
@login_required
def endtest(email=None):
    email = email if email else get_email_from_session()

    data = json.loads(cgi.escape(str(request.get_data(), 'utf-8')))
    end_test_data, testend, score, spkling = getendtestdata(data)
    
    data1 = TestDetails.query.filter_by(email = email).first()
    if data1:
        learningcenter = updatelearningcentre(email)
        updatetestdetails(data1,testend,score,learningcenter)


@app.route('/startquiz')
@login_required
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

def makestatusbutton(email,hosted):
    if hosted:
        td = TestDetails.query.filter_by(email=email).first()
        if td:
            if td.testend:
                button = "<a href='/quiz' class='btn btn-sm btn-default'>Your Score: "+str(td.score)+"</a>"
            else:
                button = "<a href='/quiz' class='btn btn-sm btn-warning'>In Progress!</a>"
        else:
            button = "<a href='/quiz' class='btn btn-sm btn-primary'>Attempt Test</a>"

    else:
        button = "<a href='#' class='btn btn-sm btn-warning' disabled>Locked</a>"
    return button

def gettestdetails(email, test_name):
    test_details = []
    result = Tests.query.filter_by(name=test_name).first()
    if result:
        test_details = str(result).split("::")
        button = makestatusbutton(email, result.isHosted())
        test_details.append(button)
        # tests.append(test_details)
    return test_details

@app.route('/studenttests', methods=['GET'])
@login_required
def studenttests(emailid=None):
    if not emailid:
        emailid = get_email_from_session()
    result = getFirstTestRecord(emailid)
    final = {"data": []}
    if result != None:
        tests = result.getTests()
        # app.logger.info([tests, type(getavailabletests(tests[0]))])
        for test in tests:
            app.logger.info(test)
            final["data"].append(gettestdetails(emailid,test))

    app.logger.info(final)
    return json.dumps(final)

def set_session(email=None, role=None):
    session['user'] = {}
    session['user']['email'] = email
    session['user']['role'] = role
    session['user']['allow_to_set_password'] = True

@app.route('/verify/<email>/<code>', methods=['GET'])
def verify_unique_code(email, code):
    if request.method == 'GET':
        email = base64.b64decode(email).decode()
        app.logger.info("Verifying code for %s with code %s"%(email, code))

        user = Users.query.filter_by(emailid=email, password=code).first()
        if user:
            try:
                user.verified = True
                db.session.add(user)
                db.session.commit()
                set_session(user.emailid)
                return render_template("set_password.html",
                    success="You are successfully activated your account.\n Please login")
            except Exception as e:
                return render_template("error.html", error=e)
        return render_template("unauthorized.html", error="Your verification code is invalid, contact admin")

def add_default_user_admin_if_not_exist():
    admin = Users.query.filter_by(user_type="admin").first()
    if admin is None:
        add_user_if_not_exist("admin@quiz.in","admin","admin",True)
        

def add_user_if_not_exist(email=None, password=generate_unique_code(), user_type="student", verified=False):
    user = Users.query.filter_by(emailid=email).first()
    if user is None:
        try:
            password = hashlib.md5(password.encode('utf-8')).hexdigest()
            user = Users(email, password, user_type, verified)
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            app.logger.error(e)
    return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Create default admin credentials if not already exists
    add_default_user_admin_if_not_exist()
    role = get_role_from_session()
    if role:
            return redirect(url_for(role))
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
                set_session(email, role)
                if role == "admin" and password == "admin":
                    return redirect(url_for("setpassword"))
                message = "You are logged in as %s" % email
                app.logger.info(["is user verified ", user.verified])
                app.logger.info("Logged in as %s with IP %s" % (email, ip_address))
                return redirect(url_for(role))
            else:
                error = "Please activate your account, using the link we sent to your registered email"
                app.logger.info("Tried to login in as %s from IP %s, but Account not activated." % (email, ip_address))
        else:
            error = "Invalid Credentials"
            app.logger.info("Tried to login in as %s from IP %s, but Invalid Credentials." % (email, ip_address))
        return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    login_log.debug("%s logged out with IP %s." % (session['user']["email"], ip_address))
    session.clear()
    # session.pop('user', None)
    # session.pop('TestID', None)
    return redirect(url_for('login'))

def sendMail(encode='Testing', code='Testing', email='rguktemailtest@gmail.com'):
    try:
        app.logger.debug("send mail function")
        body = """Dear Student,<br> This email message is sent by the online quiz portal.
        By clicking the link below you are verifying that this email belongs to you and your account will be activated.
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
    except Exception as e:
        app.logger.debug("Something went wrong in sending verification mail, please try again "+str(e))   
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
    if get_role_from_session():
        return redirect(url_for(get_role_from_session()))
    if request.method == "GET":
        login_log.debug("Get registration Form")
        return render_template('registration.html')
    elif request.method == "POST":
        login_log.debug("post registration Form")

        message = ""
        message_staus = ""
        login_log.debug("post registration Form")

        email = request.form["email"]
        exists = db.session.query(Users).filter_by(emailid=email).scalar() is not None
        # if email[-9:] != ".rgukt.in":
        #     message = "Email ID must be from RGUKT"
        #     message_staus = "danger"

        if not exists:
            code = generate_unique_code()
            user = add_user_if_not_exist(email, code,"student",False)
            if user:
                encode = base64.b64encode(email.encode()).decode()
                code = hashlib.md5(code.encode('utf-8')).hexdigest()
                app.logger.info("Verifying code for %s with code %s"%(email, code))

                sent = sendMail(encode, code, email)
                if sent:
                    app.logger.debug("an email has been sent to your email address "+email+". Please go to your inbox and click on the link to verify and activate your account")
                    message = "An email has been sent to your email address "+email+". Please go to your inbox and click on the link to verify and activate your account"
                    message_staus = "success"
                else:
                    db.session.delete(user)
                    db.session.commit()
                    app.logger.debug("Something went wrong in sending verification mail, please try again")
                    message = "Something went wrong in sending verification mail, please try again"
                    message_staus = "danger"
            else:
                app.logger.debug("Something went wrong in creating user, please try again")
                message = "Something went wrong in creating user, please try again"
                message_staus = "danger"
        else:
            message = str(email) + " already exists, Please check your inbox for verification mail or contact admin"
            message_staus = "danger"

        return render_template('registration.html', message=message, status=message_staus)

def update_password(user, password):
    try:
        user.password = hashlib.md5(password.encode('utf-8')).hexdigest()
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        app.logger.error(e)
    return False

@app.route('/setpassword', methods=['GET', 'POST'])
@login_required
def setpassword():
    if 'allow_to_set_password' not in session['user']:
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
                updated = update_password(user, password)
                if updated:
                    message = "Password successfully change, Please login"
                    return render_template('login.html', success=message)
                else:
                    message = "Password change failed, Please try again"
                    message_staus = "error"
                    return render_template("set_password.html", message=message, status=message_staus)
            else:
                message = "Your email address dosen't exist, Please register"
                message_staus = "error"
                return render_template("registration.html", message=message, status=message_staus)

        else:
            message = "Password and ConfirmPassword should match"
            message_staus = "error"

            return render_template("set_password.html", message=message, status=message_staus)

@app.route('/audio', methods=['GET', 'POST'])
@login_required
def audio():
    return render_template("audio.html")
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

def createDefaultTest():
    return redirect(url_for("create"))

def settestsession(TestID,start_date,end_date):
    try:
        session["TestID"] = TestID
        session["start_date"] = start_date
        session["end_date"] = end_date
        return True
    except Exception as e:
        app.logger.error(e)
        return redirect(url_for("error", error="settestsession: unable to save the tesr session."))

@app.route('/admin')
@admin_login_required
def admin(email=None):
    try:
        tests = Tests.query.all()
        if len(tests) != 0:
            
            return render_template('admin.html')
        else:
            return createDefaultTest()
    except Exception as e:
        return createDefaultTest()

def getFirstTestRecord(emailid):
    return StudentTests.query.filter(StudentTests.emailid == emailid).first()

def validate_name(name):
    result = Tests.query.filter_by(name=name).first()
    return result == None

#Change the the now() to utcnow() and add replace method
def validate_date(date):
    today = datetime.now(IST)
    date = IST.localize(datetime.strptime(date, '%d-%m-%Y %H:%M'))
    app.logger.info([date, today])

    return date > today

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

@app.route('/uninvite/<email>', methods=["GET"])
@admin_login_required
def uninvite(email):
    result = StudentTests.query.filter_by(emailid=email).delete()
    db.session.commit()
    return redirect(url_for('edit'))

def save_file(folder_name,file_name,data):
    filename = secure_filename(file_name)
    path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name+"/")
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, filename), "w+") as f:
        fJson.dump(data, f)
    # file.save(os.path.join(path, filename))
    # file.close()

def updatetests(test_name,email,start_date,end_dtae):
    try:
        test = Tests(test_name, email, start_date, end_date)
        db.session.add(test)
        db.session.commit()
    except Exception as e:
        app.logger.info()

@app.route('/create', methods=["GET","POST"])
@admin_login_required
def create(admin=None, test_name=None):
    if not admin:
        admin = session["user"]['email']

    if request.method == "GET":
        if not test_name:
            test_name = "English Literacy Test"
        nameValid = validate_name(test_name)

        start_date = "30-07-2017 12:00"
        startdateValid = validate_date(start_date)
        
        end_date = "30-08-2017 12:00"
        enddateValid = validate_date(end_date)

        testValid = False
        if nameValid and startdateValid and enddateValid:
            testValid = True
            app.logger.info('%s created a Test - %s' %(admin,test_name))
            settestsession(test_name,start_date,end_date)
            return redirect(url_for("admin"))
        else:
            app.logger.info('Failed to create Test - %s' %test_name)
            return redirect(url_for("admin"))

def loadTestSet():
    student = Users.query.filter_by(user_type="student").first()
    if student is None:
        for num in range(20):
            row = Users("student"+str(num)+"@quiz.in","student","student",True)
            db.session.add(row)
            db.session.commit()

def isRegistered(studentemail):
    registered = Users.query.filter(Users.emailid == studentemail).first()
    if registered:
        return registered.verified
    return False

# def Invited(studentemail,testid):
#     studentrow = StudentTests.query.filter(StudentTests.emailid == studentemail).first()
#     if studentrow != None:
#         return testid in studentrow.getTests()
#     return False

def updateDate(testid, start_date,end_date):
    test = Tests.query.filter_by(name=testid).first()
    test.start_date = start_date
    test.end_date = end_date
    db.session.commit()
    
def updateStudents(testid, students_list):
    
    slist = []
    for student in students_list:
        student = student.lstrip()
        student = student.rstrip()
        if student == "":
            continue
        if isRegistered(student):
            slist.append(student)
            qry = getFirstTestRecord(student)
            if qry != None:
                if testid in qry.testslist:
                    session["students"].append(student+" is already Invited.")
                else:
                    qry.testslist.append(testid)
                    db.session.commit()
            else:
                tests = [testid]
                studenttests = StudentTests(student,tests)
                db.session.add(studenttests)
                db.session.commit()
                session["students"].append(student+" is Invited.")
                app.logger.info('%s is Invited' %student)
        else:
            session["students"].append(student+" is not Registered.")
            app.logger.info('%s is not registered' %student)
    session["slist"] = slist

@app.route('/edit', methods=["GET", "POST"])
@admin_login_required
def edit(testid=None):

    if not testid:
        testid = testid if testid else "English Literacy Test"
        # app.logger.info('Edit Test Page (%s) accessed by %s' %(testid))

    if request.method == "GET":
        session["messages"] = False
        return render_template("add_students.html")

    if request.method == "POST":
        session["messages"] = True
        session["students"] = []
        try:
            start_date = request.form["datetimepicker1"]
            end_date = request.form["datetimepicker2"]
            if start_date != "" and end_date != "":
                validate_start_date = validate_date(start_date)
                validate_end_date = validate_date(end_date)

                if validate_start_date:
                    if validate_end_date:
                        updateDate(testid, start_date,end_date)
                    else:
                        session["startdatevalid"] = "End Date %s is not Valid." %str(end_date)
                else:
                    session["enddatevalid"] = "Start Date %s is not Valid." %str(start_date)

            students_list = request.form["studentslist"]
            if len(students_list) != 0:
                students_list = students_list.split("\n")
                app.logger.info('Students List %s' %students_list)
                updateStudents(testid, students_list)

        except Exception as e:
            session["students"].append(e)

        app.logger.info('%s added %s to %s' %(admin,session["students"],testid))
        return render_template("add_students.html")

@app.route('/getStudentsList/<test>', methods=["GET"])
@admin_login_required
def getStudentsList(test):
    # test = session["TestID"]
    result = StudentTests.query.all()
    students = []
    for i in result:
        if test in i.testslist:
            students.append(i.emailid)
    return json.dumps({"students":students})

@app.route('/prefiledit/<name>', methods=["GET"])
@admin_login_required
def prefiledit(name):
    test = Tests.query.filter_by(name=name).first()

    start_date = test.start_date
    end_date = test.end_date
    students = eval(getStudentsList(name))["students"]

    return json.dumps({"start_date":start_date, "end_date":end_date, "students":students})

def sendNotifyMail(email='rguktemailtest@gmail.com'):
    try:
        app.logger.debug("send notify mail function")
        body = """Dear Student,<br> This email message is sent by the online quiz portal.
        Click on the link below and follow the instructions to take the test.
        <a href=%s/quiz>Test Link</a> """ % (request.host)
        response = requests.post(
            "https://api.mailgun.net/v3/rguktrkv.ac.in/messages",
            auth=("api", os.environ['YOUR_MAIL_GUN_KEY']),
            data={"from": "RGUKT QUIZ <news@rguktrkv.ac.in>",
                  "to": [email],
                  "subject": 'RGUKT QUIZ LINK',
                  "text": '',
                  "html": body})
        app.logger.info([email, response.status_code, response.text])
        return response
    except Exception as e:
        app.logger.info(e)


@app.route('/notify/<testid>', methods=["GET", "POST"])
@admin_login_required
def notify(testid):
    testID = testid
    if testID == None or testID == "":
        return json.dumps([{}])

    student_emails = eval(getStudentsList(testID))['students']
    mail_responses = []
    for email in student_emails:
        response = sendNotifyMail(email=email)
        mail_responses.append({
            "mail":email,
            "status_code":response.status_code,
            "status_message":response.text
        })
    return json.dumps(mail_responses)

def get_all_test_created_by(creator=None):
    if not creator:
        return {}
    result = Tests.query.filter_by(creator=creator).all()
    final = {}
    final["data"] = []
    count = 0
    for test in result:
        count+=1
        test = str(test).split("::")
        app.logger.info(test)
        test.append(eval(getStudentsList(test[0]))["students"])
        app.logger.info(test)
        button = "<a href='/edit' class='btn btn-sm btn-primary'>Edit Test</a>"
        test.append(button)
        button = "<a href='/quiz' class='btn btn-sm btn-success'>Preview Test</a>"
        test.append(button)
        button = "<a data-toggle='modal' data-target='#NotifyMailResponses' id='notify"+str(count)+"' name='/notify/"+test[0]+"' class='btn btn-sm btn-warning'>Notify</a>"
        test.append(button)
        final["data"].append(test)

    return final

@app.route('/loadtests', methods=["GET"])
@admin_login_required
def loadtests(creator=None):
    if not creator:
        creator = get_email_from_session()
    app.logger.info("Getting all tests created by " + creator)
    final = get_all_test_created_by(creator)
    app.logger.info(str(json.dumps(final)))
    return json.dumps(final)

@app.route('/autocomplete', methods=['GET'])
@admin_login_required
def autocomplete(search=None):
    if not search:
        search = request.args.get('q')
    query = db.session.query(Users.emailid).filter(Users.emailid.like('%' + str(search) + '%'))
    results = [mv[0] for mv in query.all()]
    return jsonify(matching_results=results)

@app.route('/getAllStudentDetails', methods=['GET'])
@admin_login_required
def getAllStudentDetails():
    students = userDetails.query.all()
    student_table = {}
    for student in students:
        if student.email not in student_table:
            student_table[student.email] = {"name": student.name, "rollno":student.rollno}
    return json.dumps(student_table)

def get_test_responses_as_dict(testid=None):
        result = Response.query.all()

        students = json.loads(getAllStudentDetails())
        questions = ""
        # app.logger.info(students)
        table = {}
        for entry in result:
            id = entry.id
            name = entry.name
            rollno = ""
            emailid = entry.emailid
            pin = entry.pin
            testctime = entry.testctime
            submittedans = entry.submittedans
            responsetime = entry.responsetime
            q_score = entry.q_score
            q_status = entry.q_status
            time = entry.time
            currentQuestion = entry.currentQuestion
            serialno = entry.serialno
            if emailid in students:
                student = students[emailid]
                name = student['name']
                rollno = student['rollno']


            if rollno not in table:
                table[rollno] = {
                    "name":name,
                    "rollno":rollno,
                    "emailid":emailid,
                    "testctime":testctime,
                    "count": 1
                }

            if currentQuestion is None:
                continue

            table[rollno].update({
                            "Question_"+str(table[rollno]['count'])+"_Submittedans":submittedans,
                            "Question_"+str(table[rollno]['count'])+"_Responsetime":responsetime,
                            "Question_"+str(table[rollno]['count'])+"_Score":q_score,
                            "Question_"+str(table[rollno]['count'])+"_Status":q_status,
                            "Question_"+str(table[rollno]['count'])+"_Time":time,
                            "Question_"+str(table[rollno]['count'])+"":currentQuestion,
                        })
            table[rollno]['count'] += 1

        return table

def render_csv_from_test_responses(data):
        csvList = []
        header = [
                    "name",
                    "rollno",
                    "emailid",
                    "testctime",
                ]
        # app.logger.info(list(data)[0])

        Questions_count = db.session.query(distinct(Randomize.qno)).count()
        app.logger.info(["number is ", Questions_count])
        # return ""
        for i in range(1, Questions_count + 1):
            # app.logger.info("hi ra --> Question"+ str(i))
            header.extend(
                    [
                        "Question_"+str(i)+"",
                        "Question_"+str(i)+"_Score",
                        "Question_"+str(i)+"_Submittedans",
                        "Question_"+str(i)+"_Responsetime",
                        "Question_"+str(i)+"_Status",
                        "Question_"+str(i)+"_Time"
                    ]
                )
        csvList.append(header)

        for csv_line in data:
            app.logger.info(csv_line)
            row = [csv_line["name"],
                    csv_line["rollno"],
                    csv_line["emailid"],
                    csv_line["testctime"]
                    ]
            for i in range(1, Questions_count + 1):
                row.extend(
                        [
                            csv_line["Question_"+str(i)+""] if "Question_"+str(i)+"" in csv_line else "",
                            csv_line["Question_"+str(i)+"_Score"] if "Question_"+str(i)+"_Score" in csv_line else "",
                            csv_line["Question_"+str(i)+"_Submittedans"] if "Question_"+str(i)+"_Submittedans" in csv_line else "",
                            csv_line["Question_"+str(i)+"_Responsetime"] if "Question_"+str(i)+"_Responsetime" in csv_line else "",
                            csv_line["Question_"+str(i)+"_Status"] if "Question_"+str(i)+"_Status" in csv_line else "",
                            csv_line["Question_"+str(i)+"_Time"] if "Question_"+str(i)+"_Time" in csv_line else "",
                        ]
                    )
            csvList.append(row)
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerows(csvList)
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=English Literacy Test.csv"
        output.headers["Content-type"] = "text/csv"
        return output

@app.route('/downloadTestResults/<testid>')
def downloadTestResults(testid):
    if request.method == 'GET':

        app.logger.info(["Requested result for test with id ",testid])
        table = get_test_responses_as_dict(testid)

        data = table.values()
        return render_csv_from_test_responses(data)

@app.route('/showrecorder', methods=['GET'])
def showrecorder():
    if request.method == "GET":
        return render_template('recorder.html')

@app.route('/getrecorder', methods=['GET'])
def getrecorder():
    if request.method == "GET":
        return '<div class="container"> <div> <h3>Record: </h3> <hr> <button class="btn btn-primary" id="record">Record</button> <button class="btn btn-primary" id="stop" disabled>Stop</button> </div> <div data-type="wav"> <h3>Recorded Audio: </h3> <div id="recorded"></div> </div> <div data-type="wav"> <h3>Save Audio: </h3> <button class="btn btn-primary" id="save">Save</button> </div> </div>'

    # if request.method == "POST":


# ==================================================
                    # UNIT Tests
# ==================================================

def evaluate(name, expected, actual):
    output = {"testcase_name":name, "result":None, "response":None}
    try:
        if json.loads(actual) == json.loads(expected):
            result = "Pass"
            response = "OK"
        else:
            result = "Fail"
            response = "Expected %s got %s"%(expected, actual)
    except Exception as e:
        response = e
        result = "Fail"
    output['result'] = result
    output['response'] = response
    return output

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def test_get_test_responses_as_dict():
    output = {"function_name": inspect.stack()[0][3], "testcases":[]}
    expected = {"128": {"emailid": "sirimala.sreenath@gmail.com", "Question_5_Status": "submitted", "Question_6_Submittedans": "#", "Question_1": "102", "Question_2": "103", "Question_4_Score": 0, "Question_3_Responsetime": 2.279, "Question_3": "104", "Question_5_Score": 0, "testctime": "2017-07-08T07:45:24.463860", "Question_6": "201", "Question_2_Score": 1, "Question_6_Status": "submitted", "Question_2_Responsetime": 1.317, "Question_3_Status": "submitted", "Question_4": "105", "Question_3_Score": 0, "Question_5_Responsetime": 2.021, "Question_4_Submittedans": "None of these", "Question_5_Time": "2017-07-08T07:45:50.917283", "Question_4_Time": "2017-07-08T07:45:48.870909", "Question_1_Time": "2017-07-08T07:45:43.599523", "Question_4_Status": "submitted", "count": 7, "Question_6_Time": "2017-07-08T07:50:07.829351", "Question_3_Time": "2017-07-08T07:45:47.254924", "Question_2_Time": "2017-07-08T07:45:44.958977", "Question_2_Submittedans": "By the Prime Minister of India in an unscheduled, real time, televised address to the nation", "Question_6_Score": 0, "Question_1_Status": "submitted", "Question_1_Submittedans": "All of the above", "rollno": "128", "Question_3_Submittedans": "False", "Question_1_Score": 1, "name": "Sreenath", "Question_5_Submittedans": "Partly true", "Question_6_Responsetime": 257.088, "Question_1_Responsetime": 4.737, "Question_2_Status": "submitted", "Question_5": "106", "Question_4_Responsetime": 1.591}, "1234": {"emailid": "vy@fju.us", "Question_7_Submittedans": "#", "Question_8_Responsetime": 6.418, "Question_5": "105", "Question_3": "103", "Question_6_Time": "2017-07-08T07:42:04.291266", "Question_7_Status": "submitted", "Question_6": "106", "Question_5_Status": "submitted", "Question_2_Responsetime": 1.472, "Question_8_Score": 0, "Question_3_Score": 1, "Question_6_Responsetime": 1.89, "Question_1_Score": 0, "Question_5_Responsetime": 1.768, "count": 9, "Question_2_Time": "2017-07-08T07:41:54.570905", "Question_8_Status": "submitted", "Question_3_Submittedans": "By the Prime Minister of India in an unscheduled, real time, televised address to the nation", "Question_7_Time": "2017-07-08T07:42:06.512938", "Question_1_Status": "submitted", "Question_6_Submittedans": "True", "rollno": "1234", "name": "Veda", "Question_5_Submittedans": "Safety fee", "Question_6_Status": "submitted", "Question_8": "1", "Question_7_Responsetime": 2.181, "Question_8_Time": "2017-07-08T07:42:12.949458", "Question_7": "201", "Question_1": "101", "Question_2": "102", "Question_4_Score": 0, "Question_4": "104", "Question_5_Score": 0, "testctime": "2017-07-08T07:41:47.277874", "Question_2_Score": 0, "Question_3_Status": "submitted", "Question_8_Submittedans": "The answer to all the problems", "Question_6_Score": 0, "Question_4_Submittedans": "Not sure", "Question_5_Time": "2017-07-08T07:42:02.361560", "Question_2_Status": "submitted", "Question_1_Time": "2017-07-08T07:41:53.051284", "Question_7_Score": 0, "Question_4_Status": "submitted", "Question_3_Time": "2017-07-08T07:41:56.276504", "Question_3_Responsetime": 1.668, "Question_1_Submittedans": "3.26 million people", "Question_2_Submittedans": "Maoist extremism", "Question_1_Responsetime": 3.99, "Question_4_Time": "2017-07-08T07:42:00.559407", "Question_4_Responsetime": 4.249}}
    expected = json.dumps(expected)
    testcases = [("test1", expected, json.dumps(get_test_responses_as_dict(None), default=datetime_handler)),
        ("test2",expected,json.dumps(get_test_responses_as_dict(12), default=datetime_handler)),
        ("test3",expected,json.dumps(get_test_responses_as_dict("12"), default=datetime_handler)),
        ("test4",expected,json.dumps(get_test_responses_as_dict(16), default=datetime_handler)),
        ("test5",expected,json.dumps(get_test_responses_as_dict(122), default=datetime_handler)),]
    for testcase in testcases:
        testcase_output = evaluate(testcase[0], testcase[1], testcase[2])
        # app.logger.info(testcase_output)
        output['testcases'].append(testcase_output)
    return str(output)

def test_add_user_if_not_exist():
    output = {"function_name": inspect.stack()[0][3], "testcases":[]}
    testcases = [
        ("test1", json.dumps("{}"), add_user_if_not_exist(email=None, password="generate_unique_code", user_type="student", verified=False))
    ]
    
    for testcase in testcases:
        testcase_output = evaluate(testcase[0], testcase[1], testcase[2])
        # app.logger.info(testcase_output)
        output['testcases'].append(testcase_output)
    return str(output)

@app.route('/unit_test')
def unit_test():
    # return test_get_test_responses_as_dict()
    return test_add_user_if_not_exist()
