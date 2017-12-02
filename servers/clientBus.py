from flask import  Flask, session, render_template, request, redirect, url_for
import requests

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def test():
	if request.method == 'GET':
		reqs = requests.post('http://0.0.0.0:5000/bus')
		print reqs.text
	else:
		pass
	return render_template('index.html')

if __name__ == '__main__':

    app.run(host='0.0.0.0', port='8080',debug=False)