# Pyramid Imports
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.renderers import render_to_response
from pyramid.response import Response
import time
import json
import random

# Import MySQL Connector Driver
import mysql.connector as mysql

# Import OpenCV and NumPy
import cv2
import numpy as np

# Load the DB credentials
import os
db_host = os.environ['MYSQL_HOST']
db_user = os.environ['MYSQL_USER']
db_pass = os.environ['MYSQL_PASSWORD']
db_name = os.environ['MYSQL_DATABASE']

# Valid commands from web UI controller
valid_commands = ['takeoff','land','up','down','left',
  'right','back','forward','cw','ccw']


""" Helper Function """

# A Function to Queue Commands to the MySQL Database
def send_command(command):
  db = mysql.connect(user=db_user, password=db_pass, host=db_host, database=db_name)
  cursor = db.cursor()
  query = "insert into Commands (message, completed) values (%s, %s)"
  values = (command, "0")
  cursor.execute(query, values)
  db.commit()
  db.close()


""" Routes """

# VIEW: Web Controller Route
def web_ui_route(req):
  return render_to_response('templates/web_ui.html', [], request=req)


# REST: Drone Command Route
def drone_command_route(req):
  command = req.matchdict.get('command')
  arg = req.matchdict.get('arg')

  if command not in valid_commands:
    return {'error':'Invalid command received'}

  # Combine argument with command
  command = command if not arg else command + " " + arg[0]

  print('Sending command: ', command)
  send_command(command)
  return {'success':'Command sent!'}


def detection_data_route(req):
  #Get the latest list of objects detected
  try:
    db = mysql.connect(user=db_user, password=db_pass, host=db_host, database=db_name)
    cursor = db.cursor()
  except:
    return {"error": "No Db Connection"}
  
  # Add logic to retrieve detected objects from 'DetectedObjects' table,
  # and insert them into a table on the page.
  cursor = db.cursor()
  cursor.execute("select object from DetectedObjects;")
  record = cursor.fetchall()
  print(record)
  response = Response(body=json.dumps(record))
  db.close()
  response.headers.update({'Access-Control-Allow-Origin': '*',})
  return response



# Write incoming image frame to disk
def add_frame(req):
  # Retrieve image and filename from the POST body
  img_file = req.params['image'].file
  img_name = req.params['filename']

  # Load the image
  np_array = np.frombuffer(img_file.read(), dtype="uint8")
  frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

  # Write to file
  file_path = './public/' + img_name + '.jpg'
  cv2.imwrite(file_path, frame)

  return Response("Cool, thanks!") # not expecting a response so we can have fun :)


# REST: snapshots Command Route
def get_snapshots(req):
  command = req.matchdict.get('command')

  valid_orientations = ['front','back','left','right']

  if command not in valid_orientations:
    return {'error': 'Invalid orientation received'}

  send_command("snapshot " + command)
  
  # --------------
  # You may need a very short sleep delay to ensure images are written
  # before returning control to your client!
  time.sleep(3)
  # --------------

  print('snapshot command: ', command)
  
  # When the snapshot code finishes, you should have two files in public folder:
  # screenshot.jpg, and detected_objects.jpg   
  
  # Now you want to force the client (browser view) to reload those images.
  # You could do that by "forcing" a webpage reload -- but yuck!  That's slow....
  # or...you can find a way to get the browser to reload just the images (in place)
  
  # HOW can we get a browser to reload an image in place?  
  # Does stackoverflow know?
  # Does the google machine know?
  # Wouldn't it be cool it has been done before?  And was pretty easy?
  
  # BELOW -- return something useful to your client, so the code knows
  # that this function worked correctly.  
  
  # What information do you think you want to know on the client when this response is returned?
  # Is there any data you MUST exchange for client to proceed?
  # Does the caller need an image name? A timestamp? And object count?  Anything?
  # NOTE: Only return info the client NEEDS to proceed. Often, that's only the status code.
  
  # Of course -- we must ALWAYS return a valid response with web status code (likely 200)
  
  return {'success':'[snapshot and object detection available for use]'}

def get_target(req):
  command = req.matchdict.get('command')
  cmd = command.split("_")
  try:
    db = mysql.connect(user=db_user, password=db_pass, host=db_host, database=db_name)
    cursor = db.cursor()
  except:
    return {"error": "No Db Connection"}
  cursor = db.cursor()
  cursor.execute("select orientation from DetectedObjects where object ='{}';".format(cmd[1]))
  record = cursor.fetchall()
  db.close()
  orient = list(record[0])
  if orient[0] == 'front': #orientation of target is in front
    if cmd[0] == 'front':
      pass
    if cmd[0] == 'left':
      send_command('cw 90')
    if cmd[0] == 'right':
      send_command('ccw 90')
    if cmd[0] == 'back':
      send_command('cw 180')
  if orient[0] == 'left': #orientation of target is in left
    if cmd[0] == 'front':
      send_command('ccw 90')
    if cmd[0] == 'left':
      pass
    if cmd[0] == 'right':
      send_command('cw 180')
    if cmd[0] == 'back':
      send_command('cw 90')
  if orient[0] == 'right': #orientation of target is in right
    if cmd[0] == 'front':
      send_command('cw 90')
    if cmd[0] == 'left':
      send_command('cw 180')
    if cmd[0] == 'right':
      pass
    if cmd[0] == 'back':
      send_command('ccw 90')
  if orient[0] == 'back': #orientation of target is in back
    if cmd[0] == 'front':
      send_command('cw 180')
    if cmd[0] == 'left':
      send_command('ccw 90')
    if cmd[0] == 'right':
      send_command('cw 90')
    if cmd[0] == 'back':
      pass
  
  send_command('target ' + cmd[1])

  return {'success':'[target acquired]'}

""" Main Entrypoint """

if __name__ == '__main__':
  with Configurator() as config:
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')

    config.add_route('web_ui', '/')
    config.add_view(web_ui_route, route_name='web_ui')

    config.add_route('drone_command', '/drone_command/{command}*arg')
    config.add_view(drone_command_route, route_name='drone_command', renderer='json')

    #Route to get Drone Object Detection data
    config.add_route('get_detection', '/get_detection')
    config.add_view(detection_data_route, route_name='get_detection', renderer='json')

    #Route to get object snapshots
    config.add_route('get_snapshots', '/snapshots/{command}')
    config.add_view(get_snapshots, route_name='get_snapshots', renderer='json')

    #Route to get target
    config.add_route('get_target', '/target/{command}')
    config.add_view(get_target, route_name='get_target', renderer='json')

    # Route to save images to public folder
    config.add_route('add_frame', '/add_frame')
    config.add_view(add_frame, route_name='add_frame')

    config.add_static_view(name='/', path='./public', cache_max_age=3600)

    app = config.make_wsgi_app()

  server = make_server('0.0.0.0', 1234, app)
  print('Web server started on: http://0.0.0.0:8000 OR http://localhost:8000')
  server.serve_forever()
