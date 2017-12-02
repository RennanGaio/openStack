from flask import Flask, session, render_template, request, redirect, url_for, flash
from wtforms import Form, BooleanField, TextField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc


app = Flask(__name__)

def getpass(username):
	#fazer chamada do bd relacionando o usr a senha
	return password

class RegistrationForm(Form):

    username = TextField('Login')
    usr_type = SelectField('Tipo de usuario', choices=[('Sem deficiencias'), ('Deficiente fisico'), ('Deficiente visual'), ('Deficiente Mental'), ('idoso'), ('Cadeirante')])
    password = PasswordField('Nova senha', [
        validators.Required(),
        validators.EqualTo('Confirmar senha', message='Senha precisa bater')
    ])
    confirm = PasswordField('Repita sua senha')


# #primeiro acesso do usuario, ele ira se cadastrar no sistema
# @app.route('/register', methods=["GET","POST"])
# def register_page():
#     try:
#         form = RegistrationForm(request.form)

#         if request.method == "POST":
#             username  = form.username.data
#             usr_type = form.usr_type.data
#             password = sha256_crypt.encrypt((str(form.password.data)))
#             bd, conn = connection()

#             x = bd.execute("SELECT * FROM users WHERE username = (%s)",
#                           (thwart(username)))

#             if int(x) > 0:
#                 flash("That username is already taken, please choose another")
#                 return render_template('register.html', form=form)

#             else:
#                 bd.execute("INSERT INTO users (username, password, usr_type) VALUES (%s, %s, %s)",
#                           (thwart(username), thwart(password), thwart(usr_type)))
                
#                 conn.commit()
#                 flash("Thanks for registering!")
#                 bd.close()
#                 conn.close()
#                 gc.collect()

#                 session['logged_in'] = True
#                 session['username'] = username

#                 return redirect(url_for('dashboard'))

#         return render_template('register.html', form=form)

#     except Exception as e:
#         return(str(e))


#interface que o usuario ira usar para fazer login
#ele entra com usr e password e recebe o seu tipo de pessoa como resposta
# @app.route('/login', methods=['GET', 'POST'])
# def index():
# 	if request.method == 'GET':
# 		try:
# 			username = request.form['usr']
# 			password = request.form['password']
# 			usr_type = request.form['usr_type']
# 			if (password==getpass(username)):
# 			    return get_type(username)
# 			else:
# 				return "wrong password"
# 		except:
# 			pass
# 	return "oi rennan"


#depois de logado o usuario devera mandar a requisicao de sua localizacao com o seu tipo q recebeu no login
@app.route('/ususario', methods=['GET', 'POST'])
def indexUser():
    #return 'Hello, World!'
    error = None
    if request.method == 'POST':
    	username = request.form['usr']
    	# password = request.form['password']
    	bus_number = request.form['bus_number']
    	bus_stop_location = request.form['bus_stop_location']
    	usr_type = request.form['usr_type']
        #if (password==getpass(username)):
        expose_to_bus([bus_stop_location, usr_type])
        #else:
        #    error = 'wrong password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    #return render_template('login.html', error=error)
    return 'vc deu get'


#essa sera a url acessada pelos onibus periodicamente para verificarem se ouve atualizacao.
@app.route('/bus', methods=['GET', 'POST'])
def indexBus():
	if request.method == 'GET':
		#bus_data is a list of touples [[bus_stop1, usr_type1], [bus_stop2, usr_type2], ...]
		#get_user_info will return a list of near bus_stops sinalizeds
		bus_data=get_usr_info(request.form['bus_number'], request.form['bus_location'])
		return bus_data


if __name__ == '__main__':

    app.run(host='0.0.0.0', port='5000',debug=False)