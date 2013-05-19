import ConfigParser, os
import dateutil
import random
import hashlib
from dateutil import parser
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from flask import Flask,redirect,request
from flask import render_template
import urllib2
import correio
from flask.ext.mail import Mail, Message

config = ConfigParser.ConfigParser()
config.readfp(open('correio.cfg'))

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = config.get('Mail','user'),
    MAIL_PASSWORD = config.get('Mail','pass'),
    DEFAULT_MAIL_SENDER = 'noreply@auszug.com.br'
    )

mail = Mail(app)

engine = create_engine(config.get('Database','uri'), echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)

class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer, primary_key=True)
    oid = Column(String, primary_key=True)
    description = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref=backref("objects"))
    delivered = Column(Boolean)

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    local = Column(String)
    activity = Column(String)
    oid = Column(String, ForeignKey("objects.oid"))
    object  = relationship("Object", backref=backref("events"))

def notify_events(recipient, id, events):
    subject = 'Rastreador dos correios: '+id
    message = Message(subject,
                      sender=app.config["DEFAULT_MAIL_SENDER"],
                      recipients=[recipient])
    message.body = subject+"\n\n"
    
    for event in events:
        message.body += event["datetime"]+": "+event["local"]+"\n"
        message.body += event["activity"]+"\n\n"

    mail.send(message)
    
def fetch_events(id):
    object = session.query(Object).filter_by(oid=id).first()
    if object:
        page = urllib2.urlopen("http://websro.correios.com.br/sro_bin/txect01$.QueryList?P_LINGUA=001&P_TIPO=001&P_COD_UNI="+id)
        items = correio.parse(page.read())

        if len(items) == len(object.events): return
        
        if len(object.events) != 0:
            items = items[len(object.events):]
            
        for item in items:
            event = Event()
            event.datetime = parser.parse(item["datetime"])
            event.local = item["local"]
            event.activity = item["activity"]
            event.oid = object.oid
            session.add(event)
            if item["activity"] == "Entrega Efetuada": object.delivered = True
    session.commit()
    return items


@app.route("/")
def root():
    users = session.query(User).all()
    return render_template('index.html')

@app.route("/add", methods=["post"])
def add():
    user = session.query(User).filter_by(email=request.form["email"]).first()
    if not user:
        user = User()
        user.email = request.form["email"]
        session.add(user)

    object = session.query(Object).filter_by(oid=request.form["id"]).first()
    if not object:
        object = Object()
        object.oid = request.form["id"]
        object.user_id = user.id
        session.add(object)

    confirmation_code = hashlib.md5(user.email+str(random.random())).hexdigest()
    message = Message("Confirme o rastreamento do pacote",
                      sender=app.config["DEFAULT_MAIL_SENDER"]
                      recipients=[user.email])
    message.body = "Para confirmar o rastreamento, acesse http://tracker.auszug.com.br/confirm/"+confirmation_code
    mail.send(message)
    session.commit()
    return redirect("/")

@app.route("/confirm/<code>")
def confirm(code):
    object = session.query(Object).filter_by(confirmation_code=code).first()
    if object:
        object.confirmed = 1
        events = fetch_events(object.oid)
        if events and len(events) != 0: notify_events(user.email, object.oid, events)
        session.commit()
        return "Rastreamento confirmado"
    else:
        return "Codigo nao encontrado"

@app.route("/track/<id>")
def track(id):
    page = urllib2.urlopen("http://websro.correios.com.br/sro_bin/txect01$.QueryList?P_LINGUA=001&P_TIPO=001&P_COD_UNI="+id)
    events = correio.parse(page.read())
    return render_template('track.html', events=events)

if __name__ == "__main__":
    app.run(debug=True)
