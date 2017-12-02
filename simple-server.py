from flask import Flask, session, render_template, request, redirect, url_for

app = Flask(__name__)

def getpass(username):
	#fazer chamada do bd relacionando o usr a senha
	return password

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		username = request.form['usr']
    	password = request.form['password']
    	if (password==getpass(username)):
            return get_type(username)
        else:
        	return "wrong password"

@app.route('/register', methods=['GET', 'POST'])
def indexregister():
	global listOfBots
	#print 'try to connect'
	#print request.method
	if request.method == 'POST':
		register_user(request.form['usr'], request.form['password'])
		session.pop('user', None)
		#password has to be set in .env
		#redisVariables["wrapper.CONNECTOR_PASSWORD"]
		if request.form['password'] == passfrase:
			if (request.form['username'] not in listOfBots):
				session['user'] = request.form['username']
				registerBot(session['user'], listOfBots)
				# print 'connection complete'
				#return redirect(url_for('getsession'))
				return session['user']
			else:
				return request.form['username']
	return render_template('index.html')


@app.route('/afterLogin', methods=['GET', 'POST'])
def indexUser():
    #return 'Hello, World!'
    error = None
    if request.method == 'POST':
    	username = request.form['usr']
    	password = request.form['password']
    	bus_number = request.form['bus_number']
    	bus_stop_location = request.form['bus_stop_location']
    	usr_type = request.form['usr_type']
        if (password==getpass(username)):
            expose_to_bus([bus_stop_location, usr_type])
        else:
            error = 'wrong password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    #return render_template('login.html', error=error)
    return 'vc deu get'

@aap.route('/bus', methods=['GET', 'POST'])
def indexBus():
	if request.method == 'GET':
		#bus_data is a list of touples [[bus_stop1, usr_type1], [bus_stop2, usr_type2], ...]
		#get_user_info will return a list of near bus_stops sinalizeds
		bus_data=get_usr_info(request.form['bus_number'], request.form['bus_location'])
		return bus_data

if __name__ == '__main__':

    app.run(host='0.0.0.0', port='5000',debug=False)