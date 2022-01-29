import time                     # Time keeping
import mysql.connector as mysql # Import MySQL Connector Driver
from rktellolib import Tello    # Import new Tello Library (https://pypi.org/project/rktellolib/)
import os                       # Load the DB credentials
import threading                # Import threading
from object_detection import *  # Object detection file
import requests                 # Library to send data to web server
import cv2                      # Import OpenCV

COMMAND_DELAY = 1               # At most, send a command every COMMAND_DELAY seconds
heart_beat_freq = 10            # Keep the drone from sleeping itself
IMAGE_PROCESSING_DELAY = 0.3    # Delay between processing of each frame (seconds)
IMAGE_SIZE = (720, 960)         # Image size of the Tello image
ROTATION_THRESHOLD = 10         # Used for object following
FOV = 82                        # Obtained from the official TELLO website
target = None                   # If set to None, object following will not happen

detected_objects = []           # List of detected objects (including bounding boxes)
detected_objects_names = []     # List of detected object names
screenshot_raw = None           # The current frame
screenshot_detection = None     # The current frame with object detections

# Database credentials
db_host = os.environ['MYSQL_HOST']
db_user = os.environ['MYSQL_USER']
db_pass = os.environ['MYSQL_PASSWORD']
db_name = os.environ['MYSQL_DATABASE']


def follow_object(coord, box):
    """
    :param coord: Coordinate (x, y) of the center of the target object
    :param box:   Coordinates of the bounding box of the target object in the form [x, y, w, h]
            x: x coordinate of the top-left coordinate of the box
            y: y coordinate of the top-left coordinate of the box
            w: width of the box
            h: height of the box
    """

    #####################################################
    ###################CHALLENGE 2#######################
    x = coord[0]
    centerx = 480
    dis = x - 480
    pixperdeg = 960/82 #how many pixels per degree 960 is amount of pixels 
    if dis >= 0:
      turn = round(dis/pixperdeg)
      print('centering object')
      drone.cw(turn)
      
    if dis < 0:
      dis = abs(dis)
      turn = round(dis/pixperdeg)
      print('centering object')
      drone.ccw(turn)
    #####################################################
    #####################################################



    #####################################################
    ###################CHALLENGE 3#######################
    area = box[2] * box[3]
    move = round(area/500)
    print(move)
    drone.forward(move)
    drone.land()
    
    #####################################################
    #####################################################



    #####################################################
    ###################EXTRA CREDIT######################
    #####################################################


def process_image():
  """
  Thread to process the latest frame from the drone
  """
  global detected_objects, target, detected_objects_names, screenshot_raw, screenshot_detection
  imgproc = ImgProc() # Initialize object detection class from object_detection.py file

  while True:
    frame = drone.get_frame()
    if frame is not None:
      time.sleep(IMAGE_PROCESSING_DELAY)

      # Detect Objects
      detected_objects, screenshot_detection = imgproc.detect_objects(frame) # List of tuples containing object names/centroids and annotated image
      screenshot_raw = frame  # Copy original frame as to send later as screenshot (no rectangles)

      # Continue if no objects were detected...
      if len(detected_objects) == 0:
        continue

      # Store the names of all the detected objects
      detected_objects_names = list(list(zip(*detected_objects))[0])

      # If object follow mode is ON
      if target is not None:
        print("target is set")

        # If at least 1 object was detected
        if len(detected_objects) > 0:
          zip_list = list(zip(*detected_objects))

          # Proceed if the target object was detected
          if target in detected_objects_names:
            target_idx = detected_objects_names.index(target)
            coord = zip_list[1][target_idx] # Tuple containing 2 elements
            box = zip_list[2][target_idx] # list containing 4 elements
            follow_object(coord, box)
          else:
            print("Target not found in frame\tNo action being taken")


# Send frame to server
def send_frame(frame, name):
  if frame is not None:
    print("Sending frame to web server")
    url = "http://web-server:1234/add_frame"
    image = {"image": cv2.imencode(".jpeg", frame)[1].tobytes()}
    requests.post(url, files=image, data={"filename": name})


  # If there are newly detected objects, and they don't already exist,
def snapshot(orientation):
  global screenshot_raw, screenshot_detection, detected_objects_names

  print("Running detection and sending snapshots with boxes if detections are found")
  if len(detected_objects_names):
    for obj in detected_objects_names:
      print("Inserting detections....")
      query = "INSERT INTO DetectedObjects (object, orientation) values (%s, %s)"
      values = (obj, orientation)
      cursor.execute(query, values)
    db.commit()

    # Reset detection
    detected_objects_names.clear()

  send_frame(screenshot_raw, "screenshot")
  send_frame(screenshot_detection, "detected_objects")


# Selects selects appropriate drone command given cmd string
def send_command(cmd):
  cmd = cmd.split(" ")

  if len(cmd) == 1:
    if cmd[0] == "takeoff":
      drone.takeoff()
    elif cmd[0] == "land":
      drone.land()
  else:
    cmd_cmd = cmd[0]
    cmd_arg = cmd[1]
    if cmd_cmd == "up":
      drone.up(cmd_arg)
    elif cmd_cmd == "down":
      drone.down(cmd_arg)
    elif cmd_cmd == "left":
      drone.left(cmd_arg)
    elif cmd_cmd == "right":
      drone.right(cmd_arg)
    elif cmd_cmd == "forward":
      drone.forward(cmd_arg)
    elif cmd_cmd == "back":
      drone.back(cmd_arg)
    elif cmd_cmd == "cw":
      drone.cw(cmd_arg)
    elif cmd_cmd == "ccw":
      drone.ccw(cmd_arg)
    elif cmd[0] == "snapshot":
      snapshot(cmd_arg)
    elif cmd[0] == "target":
      global target
      target = cmd[1]
    else:
      print("Error: no match!")


""" Main Entrypoint """
if __name__ == "__main__":

  # Wait until the database is ready to establish a connection, checking it every second
  while True:
    try:
      db = mysql.connect(user=db_user, password=db_pass, host=db_host, database=db_name)
      cursor = db.cursor()
      break
    except:
      time.sleep(1)

  # Create Tello connection
  try:
    drone = Tello(debug=False, has_video=True)
    drone.connect()
  except Exception as e:
    print(e)

  img_proc_thread = threading.Thread(target=process_image)
  img_proc_thread.daemon = True
  img_proc_thread.start()

  # Enter into the main event loop
  before = time.time()
  time_last_command_sent = time.time()
  while True:
    now = time.time()
    if now - before > COMMAND_DELAY:
      before = now

      # Get the most recent command
      cursor.execute("select * from Commands where completed=0 limit 1;")
      response = cursor.fetchone()
      db.commit()

      # Check if there was a command in the queue
      if response is not None:

        time_last_command_sent = now
        print("DEBUG: Command received (dispatcher): ", response)

        send_command(response[1])

        # Mark the command as completed in DB
        cursor.execute("update Commands set completed=1 where id=%s" % response[0])

        # Commit DB changes
        db.commit()

      # Else, if time since last command > 10s, query battery to keep connection
      else:
        print("DEBUG: No commands in database queue (dispatcher)")
        if now - time_last_command_sent > heart_beat_freq:
          print("DEBUG: Query battery level to keep connection (dispatcher)")
          bat = drone.get_battery()
          print("Battery Percentage: ", bat)
          time_last_command_sent = time.time()
