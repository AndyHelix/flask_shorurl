# lib
import os,base64
from flask import Flask, render_template, session, redirect, url_for, flash, request
## flask-script
from flask.ext.script import Manager, Shell
## flask-bootstrap
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate, MigrateCommand

from datetime import datetime

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, PasswordField, validators
from wtforms.validators import Required


# config
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard'
app.config['SQLALCHEMY_DATABASE_URI'] =\
        "sqlite:///" + os.path.join(basedir, 'mysql.db')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
migrate = Migrate(app, db)

# Role and User model definition
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    shorturl = db.Column(db.String(64), unique=False, index=True)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r %r>' % (self.username, self.shorturl)

# form
class NameForm(Form):
    name = StringField("What is your nick-name?", validators=[Required()])
    submit = SubmitField('Submit')

# test

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db',MigrateCommand)
# route

@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    def shortit(i):
        return ''.join(map(lambda xx:(hex(ord(xx))[2:]),os.urandom(3)))

    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            short = shortit(user)
            #ip = "l27.0.0.1:5000/url/"
            ip = "localhost:5000/url/"
            user = User(username=form.name.data, shorturl=ip+short)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        #return redirect(url_for('index'))
        return redirect(url_for('out',urls=base64.encodestring(session['name'])))
        #return redirect(url_for('out',urls=r'aHR0cDovL3d3dy5iYWlkdS5jb20=\n'))
    print "....................."
    #user = User.query.filter_by(username=session.get('name')).first()
    return render_template('index.html',
            #user=User.query.filter_by(username=session.get('name')).first(),
            form = form, name=session.get('name'),known = session.get('known', False))

@app.route('/out/<urls>')
def out(urls):
    #user = User.query.filter_by(username=base64.decodestring(urls)).first()
    urlname = base64.decodestring(urls)
    user = User.query.filter_by(username=urlname).first()
    return render_template('result.html',user=user, urlname=urlname)

    #return "<h1>%r</h1>" % base64.decodestring(urls)
    #return "<h1>%r</h1>" % base64.encodestring(urls)

@app.route('/user/<name>')
def users(name):
    return render_template('user.html', name=name)
    #return '<h1>Mitochondria!</h1>'

@app.route('/geo')
def geo():
    return render_template('geolocation.html')

@app.route('/url/<urlname>')
def url(urlname):
    OS_PATH = 'localhost:5000/url/'
    urldata = User.query.filter_by(shorturl=(OS_PATH+urlname)).first()
    url = urldata.username
    return redirect(url)

@app.route('/list')
def list():
    urllist=User.query.order_by('-id')
    return render_template('list.html',urllist=urllist)

# run app
if __name__ == '__main__':
    #app.run(debug=True)
    manager.run()
