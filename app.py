from flowdock import JSONStream
import requests
import urllib
import random
import yaml

from qdb import QuoteParser

fd = open('./config.yml','r')
config_yml = yaml.load(fd)
fd.close()

api_token = config_yml.get('FLOWDOCK',{}).get('API_TOKEN')

random_giphy = 'http://api.giphy.com/v1/gifs/random?api_key=dc6zaTOxFJmzC'
random_qdb = 'http://qdb.us/qdb.xml?action=random&fixed=0&client=github.com/keyosk/flowdock-bot'

# Incase of emergency

# requests.delete('https://<API_TOKEN>:blarg@api.flowdock.com/flows/<ORG>/<FLOW_NAME>/messages/<MESSAGE_ID>')

org = config_yml.get('FLOWDOCK',{}).get('ORGANIZATION')

fetch_flows = ['%s/%s' % (org, flow,) for flow in config_yml.get('FLOWDOCK',{}).get('FLOWS',[])]

flows = requests.get('https://%s:blarg@api.flowdock.com/flows' % api_token).json()
users = requests.get('https://%s:blarg@api.flowdock.com/users' % api_token).json()

def getFlowNameFromId(id):
  return [x for x in flows if x['id'] == id][0]['parameterized_name']

def getUserNameFromID(id):
  return [x for x in users if x['id'] == id][0].get('nick','')

def postMessageToFlow(flow_name, content, thread_id = None):
  try:

    message_data = {
      'event':'message',
      'content':content,
      'external_user_name': 'FlowBot'
    }

    if thread_id != None:
      message_data['thread_id'] = thread_id

    requests.post('https://%s:blarg@api.flowdock.com/flows/%s/%s/messages' % (api_token, org, flow_name, ), data = message_data)

  except:
    pass

def getGiphyUrlFromTag(tag):
  
  _tag = ''

  try:
    _tag = urllib.quote_plus(tag)
  except:
    pass

  try:
    if len(_tag) != 0:
      giphy = requests.get(random_giphy + '&tag=%s' % _tag).json().get('data',{}).get('image_original_url','')
    else:
      giphy = requests.get(random_giphy).json().get('data',{}).get('image_original_url','')  
  except:
    giphy = 'Failed to find something funny. Whoops.'
    print 'Failed to find something for the following tag: %s' % _tag
    pass

  return giphy


qdb_parser = QuoteParser()

def getRandomQuote():
  try:
    # Raises StopIteration
    quote = qdb_parser.getRandomQuote()
  except:
    try:
      # Who knows what could happen here? Connection issues, parser issues...
      qdb_parser.parse(requests.get(random_qdb))
      quote = qdb_parser.getRandomQuote()
    except BaseException as e:
      quote = 'Failed to find something funny. Whoops.'
      print 'QDB Error: <%s>: %s' % (type(e).__name__, e)

  return quote


stream = JSONStream(api_token)
gen = stream.fetch(fetch_flows)

for data in gen:
  if isinstance(data, dict):
    if data.get('event','') == 'message':

      thread_id = data.get('thread_id', None)
      flow_name = 'main'
      user_name = 'FlowBot'
      command = ''
      command_args = ''
      message = ''

      try:
        command = data.get('content','')[1:]
        command_args = command.split(' ', 1)
        if len(command_args) > 1:
          command = command_args[0]
          command_args = command_args[1]
        else:
          command_args = ''
      except:
        pass

      if (len(command) == 0):
        continue

      try:
        flow_name = getFlowNameFromId(data.get('flow'))
        user_name = getUserNameFromID(int(data.get('user')))
      except:
        pass

      if command == 'giphy':

        try:
          message = getGiphyUrlFromTag(command_args)
        except:
          pass

      elif command == 'qdb':

        try:
          message = getRandomQuote()
        except:
          pass

      elif command == 'roll':

        try:
          message = '%s rolled: %s' % (user_name, random.randint(0, 100),)
        except:
          pass

      elif command == 'dance':

        try:
          if len(command_args) > 0:
            message = '%s bursts into dance with %s~' % (user_name, command_args)
          else:
            message = '%s bursts into dance~' % (user_name,)
        except:
          pass

      elif command in ['vomit','barf','shit','poop']:

        try:
          if len(command_args) > 0:
            message = '%s %ss all over %s. Gross!' % (user_name, command, command_args)
          else:
            message = '%s %ss all over the place. Gross!' % (user_name, command,)
        except:
          pass

      elif command == 'sandwich':

        try:
          if len(command_args) > 0:
            message = '%s makes a tasty sandwich for %s' % (user_name, command_args)
          else:
            message = 'FlowBot makes a tasty sandwich for %s' % user_name
        except:
          pass

      elif command == 'chuck':

        try:
          message = requests.get('http://api.icndb.com/jokes/random').json().get('value',{}).get('joke','')
        except:
          pass

      if len(message) > 0:
        postMessageToFlow(flow_name, message, thread_id)