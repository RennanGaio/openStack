from flask import  Flask, session, render_template, request, redirect, url_for
import requests

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def test():
	if request.method == 'GET':
		reqs = requests.get('http://0.0.0.0:3000/bus')
		print reqs.text
	else:
		pass
	return 'hello'

if __name__ == '__main__':

    app.run(host='0.0.0.0', port='4000',debug=False)