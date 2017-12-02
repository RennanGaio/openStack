from flask import Flask, session, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    #return 'Hello, World!'
    error = None
    if request.method == 'POST':
        if (request.form['username'] == 'oi' and request.form['password'] == 'mundo'):
            return 'logadasso'
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    #return render_template('login.html', error=error)
    return 'vc deu get'

if __name__ == '__main__':

    # PORT = int(os.getenv('VCAP_APP_PORT', '5000'))
    # HOST = str(os.getenv('VCAP_APP_HOST', '0.0.0.0'))#quero mudar auqi htps://localhost/
    # print "HOST:" ,  HOST
    # print "PORT" , PORT

    app.run(host='0.0.0.0', port='5000',debug=False)