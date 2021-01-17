from flask import Flask, redirect, url_for, abort, render_template
from markupsafe import escape


app = Flask(__name__)

MAX_GREETING_COUNT = 100
REALLY_TOO_MANY_GREETING_COUNT = 1000


@app.route('/')
def hello_world():
	return 'Hello, world!'


## передаём сюда аргументы через путь <converter:name>
@app.route('/hello/<string:username>/')
@app.route('/hello/<string:username>/<int:num>')
def personal_greetings(username, num=1):
	if num >= REALLY_TOO_MANY_GREETING_COUNT:
		abort(404)
	if num > MAX_GREETING_COUNT:
		return redirect(url_for("personal_greetings", username = username,\
			num=MAX_GREETING_COUNT))
	greetings = [f"Hello " + escape(username)] * num
	return '<br/>'.join(greetings)


@app.errorhandler(404)
def page_not_found(error):
	return render_template('page_not_found.html'), 404