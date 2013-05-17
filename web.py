import ConfigParser, os
import dateutil
from dateutil import parser
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from flask import Flask,redirect,request
from flask import render_template
import urllib2
import correio

config = ConfigParser.ConfigParser()
config.readfp(open('correio.cfg'))

app = Flask(__name__)

engine = create_engine(config.get('Database','uri'), echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    # objects = relationship("Object", backref="user_id")
    

class Object(Base):
    __tablename__ = "objects"
    id = Column(Integer, primary_key=True)
    oid = Column(String, primary_key=True)
    description = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref=backref("objects"))

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    local = Column(String)
    activity = Column(String)
    oid = Column(String, ForeignKey("objects.oid"))
    object  = relationship("Object", backref=backref("events"))

def fetch_events(id):
    object = session.query(Object).filter_by(oid=id).first()
    if object:
        page = urllib2.urlopen("http://websro.correios.com.br/sro_bin/txect01$.QueryList?P_LINGUA=001&P_TIPO=001&P_COD_UNI="+id)
        items = correio.parse(page.read())

        if len(items) == len(object.events): return

        for item in items[:(len(object.events)-len(items))]:
            event = Event()
            event.datetime = parser.parse(item["datetime"])
            event.local = item["local"]
            event.activity = item["activity"]
            event.oid = object.oid
            print object.id
            print id
            session.add(event)
        session.commit()


@app.route("/")
def root():
    users = session.query(User).all()
    return render_template('index.html', users=users)

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

    fetch_events(object.oid)
    session.commit()
    return request.form["email"]
    return redirect("/")

@app.route("/track/<id>")
def track(id):
    page = urllib2.urlopen("http://websro.correios.com.br/sro_bin/txect01$.QueryList?P_LINGUA=001&P_TIPO=001&P_COD_UNI="+id)
    events = correio.parse(page.read())
    return render_template('track.html', events=events)

if __name__ == "__main__":
    app.run(debug=True)
