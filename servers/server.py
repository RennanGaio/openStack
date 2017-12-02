# -*- coding: utf-8 -*-
from flask import Flask, session, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from crawl_rates import *
from history_module import *
from activity_module import *
from informationexplored_module import *
import traceback
import json, math, os
import traceback
import yaml
import redis
import datetime
from datetime import timedelta
import requests
import re

import logging
logging.basicConfig()

#Para retirar o log
#import logging
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)
securityEnabled = False

app = Flask(__name__)

#NOTE: Session do not work here
# because there is no cookie being recorded
# The history array will store all the sessions separated
# by room
history = []

# The following array store the vars for the activity detection
history_activity_vars = []

# Information Explored: MATRIX
# THIS MATRIX IS SEPARATED BY EACH ROOM
matrix_InfoExplored = []

# Hostname. 0.0.0.0 if it is local
HOST = ""

sched = BackgroundScheduler()

taxa_poupanca = 0
taxa_di = 0
taxa_selic = 0
taxa_tr = 0

BOT_NAME = ''

# Context (activity) env vars
workspace_id_conselheiro = None
ThU_low = None
ThU_normal_min = None
ThU_normal_max = None
ThU_high = None

def roundHundreds(value):
   return int(value - value%100)

def roundTens(value):
   return int(value - value%10)

def getApproximate(value, profit, ratio):
   toBeRounded = value + profit*ratio
   rounded = roundHundreds(toBeRounded)
   roundedTens = roundTens(toBeRounded)

   if int(value) == int(toBeRounded):
      return int(value)
   elif toBeRounded >= 1000 and rounded > value:
      return rounded
   elif roundedTens > value:
      return roundedTens
   else:
      return int(toBeRounded)

mainRoute = '/'
if securityEnabled:
	listOfBots=[]
	app.secret_key = os.urandom(24)

	mainRoute = '/protected'

	#functions that will help the auth
	def registerBot (bot, listOfBots):
		if bot not in listOfBots:
			listOfBots.append(bot)
		return listOfBots

	def removeBot (bot, listOfBots):
		if bot in listOfBots:
			listOfBots.remove(bot)
		return listOfBots

	@app.route('/', methods=['GET', 'POST'])
	def index():
		global listOfBots
		#print 'try to connect'
		#print request.method
		if request.method == 'POST':
			session.pop('user', None)
			#password has to be set in .env
			#redisVariables["wrapper.CONNECTOR_PASSWORD"]
			passfrase = redisVariables["wrapper.CONNECTOR_PASSWORD"]
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

	@app.route('/getsession')
	def getsession():
		# print listOfBots
		if 'user' in session:
			return session['user']

		return 'Not logged in!'

	@app.route('/dropsession')
	def dropsession():
		global listOfBots
		removeBot(request.form['username'], listOfBots)
		session.pop('user', None)
		return 'Dropped!'

@app.route(mainRoute, methods=['GET', 'POST'])
def RequestToConversation():
    try:
        global BOT_NAME

        # Disabling the security if running local
        # This is the case when there is an unit testing running
        if HOST != '0.0.0.0':
            if securityEnabled:
                #auth acess control
                global listOfBots
                # print listOfBots
                # print 'access to protected'

                if  (request.form['username'] not in listOfBots):
                    return redirect(url_for('index'))

        #after auth, normal request

        cxt = dict()
        if request.method == 'POST':
            payload = json.loads(request.args.get('payload', ''))


            if('bot_name' in payload):
                #print "BOT_NAME:", payload['bot_name']
                BOT_NAME = payload['bot_name']
                # print "BOT_NAME set"
            #else:
                # print "BOT_NAME NOT set"
            #print payload['input']['text'].encode("utf-8")

            # data = json.loads(request.args.get('data',''))
            # dialog = request.args.get('dialog','')
            # context = request.args.get('context','')

            if 'text' in payload['input']:

                # Store the user History. Control to store only
                # the first message of the utternace
                StoreUserHistory(payload,'UI',history,history_activity_vars,matrix_InfoExplored, redisVariables)

                text = payload['input']['text']

                if 'context' in payload:
                    cxt = payload['context']
                else:
                    cxt = None

                workspace = payload['workspace_id']

                # Here I check for the activity in the message
                result_activity = CheckActivityInMsg(payload,text,workspace,cxt,workspace_id_conselheiro,history_activity_vars,ThU_high,ThU_normal_min,ThU_normal_max,ThU_low,history,matrix_InfoExplored,redisVariables)

                if result_activity!= "":
                    return result_activity

                # THIS IS THE MOST IMPORTANT PART OF THE WRAPPER:
                # CALLING THE WCS TO GET THE ANWSER
                # IMPORTANT! IMPORTANT! IMPORTANT! IMPORTANT!
                # Calling the WCS to get the anwser
                result = json.dumps(conversation_wrapper(text, cxt, workspace,redisVariables))
                #result = conversation_csb(text, BOT_NAME, redisVariables)
                output = json.loads(result, encoding='utf8')

                # Check if the bots can talk in this turn
                # Controlled by the 'variable' my_counter in the history
                # if (checkBotsOnMute(payload,history,output)):
                #     # # Do not store the message in the log and
                #     # # do now show it on the UI
                #     #print "Bots on mute"
                #     output['output']['text'][0] = 'lixo'
                #     return json.dumps(output, ensure_ascii=False)

                # FROM NOW ON HANDLE SPECIAL CASES
                # READING THE CONTENT OF THE ANWSER

                # If WCS return more than one text get the last item.
                # This happens on the begin_start intent
                if len(output['output']['text']) > 1 and output['intents'][0]['intent']  == 'begin':
                    last_item = len(output['output']['text'])-1
                    output['output']['text'][0] = output['output']['text'][last_item]

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)


                    # Storing in the history
                    StoreBotHistory(payload,output,'WCS',history,history_activity_vars,matrix_InfoExplored,redisVariables)

                    return json.dumps(output, ensure_ascii=False)


                # if output['output']['text'][0] == 'investir':
                if 'tipo' in output['context'] and output['context']['tipo'] in ['poup', 'cdb', 'tesouro'] and output['intents'][0]['intent'] in ['invest_valor_tempo', 'especifica_tempo', 'especifica_valor_tempo'] and len(output['output']['text']) > 0:

                    params = output['output']['text']
                    value = float(output['context']['valor'])
                    toCalc = calculaPoup(value, output['context']['tempo'],
                                         output['context']['tempo_ref'], output['context']['tipo'])
                    if toCalc==0:
                        value1 = 0
                        value2 = 0
                    else:
                        value1 = getApproximate(value, toCalc-value, 0.9)
                        value2 = getApproximate(value, toCalc-value, 1.1)

                    toCalc = round(toCalc, 2)

                    if (value2 - value1) >= 10:
                       # Formating the value to insert the . as separator
                       # in the calculated value
                       v1 = "{:,}".format(value1).replace(",",".")
                       v2 = "{:,}".format(value2).replace(",",".")

                       output['output']['text'][0] = output['output']['text'][0].replace('__VALOR_FINAL__', 'entre R$ ' + v1 + ' e R$ ' + v2 )
                    else:
                       # Formating the value to insert the . as separator
                       # in the calculated value
                       computed_value = getApproximate(value, toCalc-value, 1.0)

                       if computed_value > int(value):
                          v_final = "{:,}".format(computed_value).replace(",",".")
                          output['output']['text'][0] = output['output']['text'][0].replace('__VALOR_FINAL__', 'aproximadamente R$ ' + v_final )
                       else:
                          output['output']['text'][0] = output['output']['text'][0].replace('__VALOR_FINAL__', 'apenas o valor investido' )

                    # Now format the monetary value entered by the user
                    output['output']['text'][0] = formatValue(output['output']['text'][0],'.* (.+?) durante')

                    #Formating the time
                    output['output']['text'][0] = formatValue(output['output']['text'][0],'.*durante (.+?) ')

                    #Storing the values for latter
                    output['output']['val1'] = value1
                    output['output']['val2'] = value2

                    output['output']['speech_act'] = "inform_calculation"

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)

                    # Check for any closing messages
                    output = StoreBotHistoryCheckClosing(payload,output,'WCS',cxt,workspace_id_conselheiro,history,history_activity_vars,matrix_InfoExplored,redisVariables)

                    return json.dumps(output, ensure_ascii=False)

                elif 'tipo' in output['context'] and output['context']['tipo'] in ['invest'] and output['intents'][0]['intent'] in ['especifica_valor_tempo'] and len(output['output']['text']) > 0:

                    output['output']['speech_act'] = "query_calculation"

                    # Now format the monetary value entered by the user
                    output['output']['text'][0] = formatValue(output['output']['text'][0],'seria (.+?) durante')

                    #Formating the time
                    output['output']['text'][0] = formatValue(output['output']['text'][0],'.*durante (.+?) ')

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)


                    # print "Speech Act QUERY CALC"

                    # Check for any closing messages
                    output = StoreBotHistoryCheckClosing(payload,output,'WCS',cxt,workspace_id_conselheiro,history,history_activity_vars,matrix_InfoExplored,redisVariables)
                    return json.dumps(output, ensure_ascii=False)

                elif output['intents'][0]['intent'] in ['valor_taxa_selic'] and len(output['output']['text']) > 0:
                    output['output']['text'][0] = output['output']['text'][0].replace('__VALOR_SELIC__', str(taxa_selic).replace('.',',') + '% ao ano')

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)


                    # Storing in the history
                    StoreBotHistory(payload,output,'WCS',history,history_activity_vars,matrix_InfoExplored,redisVariables)

                    return json.dumps(output, ensure_ascii=False)
                elif output['intents'][0]['intent'] in ['valor_taxa_di'] and len(output['output']['text']) > 0:
                    output['output']['text'][0] = output['output']['text'][0].replace('__VALOR_DI__', str(taxa_di).replace('.',',') + '% ao ano')

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)



                    # Storing in the history
                    StoreBotHistory(payload,output,'WCS',history,history_activity_vars,matrix_InfoExplored,redisVariables)


                    return json.dumps(output, ensure_ascii=False)
                elif output['intents'][0]['intent'] in ['valor_taxa_tr'] and len(output['output']['text']) > 0:
                    output['output']['text'][0] = output['output']['text'][0].replace('__VALOR_TR__', str(taxa_tr).replace('.',',') + '% ao mês')

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)



                    # Storing in the history
                    StoreBotHistory(payload,output,'WCS',history,history_activity_vars,matrix_InfoExplored,redisVariables)

                    return json.dumps(output, ensure_ascii=False)
                else:

                    # Checking for duplicated responses for the
                    # same bot in the same turn counter
                    # if (checkDupplicatedMessageFromTail(payload,output,history,workspace_id_conselheiro)):
                    #     # Do not store the message in the log and
                    #     # do now show it on the UI
                    #     output['output']['text'][0] = 'lixo'
                    #     return json.dumps(output, ensure_ascii=False)


                    # Check for any closing messages
                    output = StoreBotHistoryCheckClosing(payload,output,'WCS',cxt,workspace_id_conselheiro,history,history_activity_vars,matrix_InfoExplored,redisVariables)

                    return json.dumps(output, ensure_ascii=False)
            else:
                return "Error: empty input"

    except:
        print "Error in Wrapper:", sys.exc_info()
        print "Traceback:", traceback.print_stack()

#redirect function
@app.before_request
def before_request():
    #print "URL antes: "+request.url
    if (not('localhost' in request.url)) and not(request.headers.get('X-Forwarded-Proto')=='https'):
        url = request.url.replace('http', 'https', 1)
        #print "URL depois: "+url
        return redirect(url)

# Format the values (insert the . as thousand separator
# Uses a Regular expression to find the value to be formated
def formatValue(text,RE):
    formated_ret = text

    m = re.search(RE, text)
    if m:
        # TODO: Handle the case when the user use a
        # decimal value separated by ","

        separatedNumber = m.group(1)
        n = re.search('(\\d+)', separatedNumber)

        if n:
            found = n.group(1).replace(',', '').replace('.', '')
            found = int(found)

            formated_value = "{:,}".format(found).replace(",",".")

            formated_ret = formated_ret.replace(n.group(1),formated_value)

    return formated_ret

def conversation_csb(text, bot_name,redisVariables):
    #wcsenv = finch-dev or wcsenv = finch-master
    wcsenv = redisVariables["wrapper.WCS_ENV"]
    print "wcsenv", wcsenv
    print "calling csb with :", "https://csb.w3ibm.mybluemix.net/" + wcsenv
    data={"bot_name": bot_name, "text":text}
    print " ..... for data : ",  data
    resp = requests.post("https://csb.w3ibm.mybluemix.net/" + wcsenv, data)
    return resp.content

#Deprecated, using CSB endpoint instead
def conversation_wrapper(text, context, workspace_id,redisVariables):
    from watson_developer_cloud import ConversationV1
    import yaml

    conversation = ConversationV1(
        username=redisVariables["wrapper.CONVERSATION_USERNAME"],
        password=redisVariables["wrapper.CONVERSATION_PASSWORD"],
        version='2016-09-20'
    )

    response = conversation.message(
        workspace_id=workspace_id,
        message_input={'text': text},
        context=context
    )
    return response



def calculaPoup(valor, tempo, tempo_ref,type):
    # M = P . (1 +  i)n

    if(valor <=0 or tempo<=0):
        return 0

    if(type == "poup"):
        taxa = float(taxa_poupanca) / 100
    elif type == "cdb":
        taxa = ((float(taxa_di)*0.96)/12) / 100
    elif type == "tesouro":
        taxa = (float(taxa_selic)/12) / 100
        #taxa = round(taxa,2)
    value = float(valor)

    try:  # the crazy conversation sometimes give the param as a string.
        interval = float(tempo)
    except:
        interval = tempo

    #convert days and years to months
    if tempo_ref == 'dia' or tempo_ref == 'dias':
        interval = interval / 30

    elif tempo_ref == 'anos' or tempo_ref == 'ano':
        interval = interval * 12

    M = value * (math.pow(1 + taxa, interval))

    #compute taxes and fees
    if type in ['cdb', 'tesouro']:
       profit = M - value
       if interval >= 0 and interval <= 6:
          taxes = profit * 0.225
       elif interval >= 7 and interval <= 12:
          taxes = profit * 0.20
       elif interval >= 13 and interval <= 24:
          taxes = profit * 0.175
       elif interval >= 25:
          taxes = profit * 0.15

       M = M - taxes

       #compute tesouro custody
       if type in ['tesouro']:
          proportion = interval/12
          M = M - M*0.003*proportion

    return M

@sched.scheduled_job('interval', hours=1) #every day 12H
def update_rates():
    taxa_poupanca = float(fetch_poupanca())
    taxa_di = float(fetch_di())
    taxa_selic = float(fetch_selic_diaria())
    taxa_tr = float(get_tr(taxa_poupanca))

    # Limpando o historico
    clean_old_history(history,history_activity_vars,matrix_InfoExplored)


def getRedisVariables():
    _redisVariables = dict()
    print ('getting redisVariables from %s ...' % os.getenv('REDIS_URL'))
    redisClient = redis.from_url(os.getenv('REDIS_URL'))

    # Getting all the variables needed here (including wrapper e connector)
    for key in redisClient.keys(pattern='*'):
        _redisVariables[key]=redisClient.get(key)
    print 'done.'

    return _redisVariables

# Here I check and load de activity environment variables
if __name__ == '__main__':

    redisVariables = getRedisVariables()

    PORT = int(os.getenv('VCAP_APP_PORT', '5000'))
    HOST = str(os.getenv('VCAP_APP_HOST', '0.0.0.0'))#quero mudar auqi htps://localhost/
    print "HOST:" ,  HOST
    print "PORT" , PORT

    taxa_poupanca = float(fetch_poupanca())
    print taxa_poupanca
    taxa_di = float(fetch_di())
    print taxa_di
    taxa_selic = float(fetch_selic_diaria())
    print taxa_selic
    taxa_tr = float(get_tr(taxa_poupanca))
    print taxa_tr

    #Get the activity vars used to check the time diff (in secs)
    ret = load_activity_vars(redisVariables)

    workspace_id_conselheiro = ret['workspace_id_conselheiro']
    ThU_low = int(ret['ThU_low'])
    ThU_normal_min = int(ret['ThU_normal_min'])
    ThU_normal_min = int(ret['ThU_normal_max'])
    ThU_high = int(ret['ThU_high'])

    # Set the intial values of the matrix for information explored
    initializeInformationExplored()

    sched.start()

    #if securityEnabled:
    #   import ssl
    #   context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #   context.load_cert_chain('cert/cert.pem', 'cert/key.pem')
    #   app.run(host=HOST, port=PORT,debug=True, ssl_context=context)
    #else:
    app.run(host=HOST, port=PORT,debug=False)