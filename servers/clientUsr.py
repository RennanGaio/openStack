from flask import  Flask, session, render_template, request, redirect, url_for
import requests

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def test():
	if request.method == 'POST':
		print request.form
		data =  {'usr': request.form['usr'], 'bus_number': request.form['bus_number'], 'bus_stop_location': request.form['bus_stop_location'], 'usr_type': request.form['usr_type']} 
		reqs = requests.post('http://0.0.0.0:5000/usuario', data = data)
		# print reqs.text
	else:
		pass
	return render_template('mainUser.html')



if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8000',debug=False)




