from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import math
import os
from datetime import datetime

with open('config.json', 'r') as c:
	parameters = json.load(c)["parameters"]


local_server="True"
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = parameters['upload_location']
app.config.update(
	MAIL_SERVER = 'smtp.gmail.com',
	MAIL_PORT = '465',
	MAIL_USE_SSL = True,
	MAIL_USERNAME = parameters ['gmail_user'],
	MAIL_PASSWORD = parameters ['gmail_password']
)
mail = Mail(app)

if(local_server):
	app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']
else:
	app.config['SQLALCHEMY_DATABASE_URI'] = parameters['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
	srno = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=False, nullable=False)
	email = db.Column(db.String(120), nullable=False)
	phone_no = db.Column(db.String(120), nullable=False)
	message = db.Column(db.String(120), nullable=False)
	date = db.Column(db.String(120))

class Posts(db.Model):
	srno = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(80), nullable=False)
	tagline = db.Column(db.String(100))
	slug = db.Column(db.String(120), nullable=False)
	posted_by = db.Column(db.String(120), nullable=False)
	content = db.Column(db.String(120), nullable=False)
	img_file = db.Column(db.String(120))
	date = db.Column(db.String(120))

@app.route('/dashboard', methods = ['GET','POST'])
def signin():

	if 'user' in session and session['user'] == parameters['admin_user']:
		post = Posts.query.all()
		return render_template('dashboard.html', parameters=parameters, posts=post)

	if request.method == 'POST':
		username = request.form.get('uname')
		password = request.form.get('pass')
		if username == parameters['admin_user'] and password == parameters['admin_password']:
			session['user'] = username
			post = Posts.query.all()
			return render_template('dashboard.html', parameters=parameters, posts=post)

	return render_template('signin.html', parameters=parameters)

@app.route('/edit/<string:srno>', methods=['GET','POST'])
def edit(srno):
	if 'user' in session and session['user'] == parameters['admin_user']:
		if request.method == 'POST':
			title = request.form.get('title')
			tagline = request.form.get('tagline')
			slug = request.form.get('slug')
			posted_by = request.form.get('posted_by')
			content = request.form.get('content')
			img_file = request.form.get('img_file')
			date = datetime.now()

			if srno == '0':
				post = Posts(title=title, tagline=tagline, slug=slug, posted_by=posted_by,
							 content=content, img_file=img_file, date=datetime.now())
				db.session.add(post)
				db.session.commit()
			else:
				post = Posts.query.filter_by(srno=srno).first()
				post.title = title
				post.tagline = tagline
				post.slug = slug
				post.posted_by = posted_by
				post.content = content
				post.img_file = img_file
				db.session.commit()
				return redirect('/edit/' + srno)
		post = Posts.query.filter_by(srno=srno).first()
		return render_template('edit.html',parameters=parameters,srno=srno,post=post)

@app.route('/uploader', methods = ['GET','POST'])
def uploader():
	if 'user' in session and session['user'] == parameters['admin_user']:
		if request.method == 'POST':
			f = request.files['file1']
			f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
		return 'uploaded successfully'

@app.route('/logout')
def logout():
	session.pop('user')
	return redirect('/dashboard')

@app.route('/delete/<string:srno>', methods=['GET','POST'])
def delete(srno):
	if 'user' in session and session['user'] == parameters['admin_user']:
		post = Posts.query.filter_by(srno=srno).first()
		db.session.delete(post)
		db.session.commit()
	return redirect('/dashboard')

@app.route('/')
def home():
	post = Posts.query.filter_by().all()
	last = math.ceil(len(post)/int(parameters['no_of_post']))
	page = request.args.get('page')
	if (not str(page).isnumeric()):
		page = 1
	page = int(page)
	post = post[(page-1)*int(parameters['no_of_post']): (page-1)*int(parameters['no_of_post'])+ int(parameters['no_of_post'])]
	#pagination logic
	# if on first page
	if (page == 1) :
		prev = "#"
		next = "/?page=" + str(page + 1)
	# if on last page
	elif (page == last) :
		prev = "/?page=" + str(page - 1)
		next = "#"
	# if on any middle page
	else:
		prev = "/?page=" + str(page - 1)
		next = "/?page=" + str(page + 1)


	return render_template('index.html', parameters=parameters, posts=post, prev=prev, next=next)

@app.route('/about')
def about():
	return render_template('about.html', parameters=parameters)

@app.route('/contact', methods = ['GET','POST'])
def contact():
	if (request.method == 'POST'):
		name = request.form.get ('name')
		email = request.form.get ('email')
		phone = request.form.get('phone')
		message = request.form.get('message')
		entry = Contacts(name=name, email=email, phone_no=phone, message=message, date=datetime.now())
		db.session.add(entry)
		db.session.commit()
		mail.send_message('New message form' + name,
						  sender = email,
						  recipients = [parameters ['gmail_user']],
						  body = message + "\n" + phone
						  )

	return render_template('contact.html', parameters=parameters)

@app.route("/post/<string:posts_slug>", methods = ['GET'])
def post_route(posts_slug):
	post = Posts.query.filter_by(slug=posts_slug).first()
	return render_template('post.html', parameters=parameters, post=post)


app.run(debug=True)