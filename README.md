# Lab 6 - Object Detection

## Due Date

Friday 3/12 11:59PM PST

## Prerequisites

This lab builds on the concepts of the previous labs. Please make sure to have watched all of these videos. Please refer to the videos if you are stuck on any part of the lab.

1) Video lecture on [HTML](https://www.youtube.com/watch?v=Ht5nE2l4mJI)
2) Video lecture on [Web Serving Fundamentals](https://www.youtube.com/watch?v=5a0R2yiiEeo)
3) Video lecture on [REST](https://www.youtube.com/watch?v=YHZmSlF-rOU)
4) Video lectures on Javascript
    1) [Introduction to Javascript](https://www.youtube.com/watch?v=E0_pEASqB3A&feature=emb_title)
    2) [Interactions](https://www.youtube.com/watch?v=Mwf_qU6zQfo)
    3) [Asynchronous javascript + JSON](https://www.youtube.com/watch?v=eusDs93MlnQ)
5) DB Intro Videos(Pick one of these):
    1) Intro to Database [Video](https://youtu.be/3_GMPJFF1sI)
    2) Advanced Intro to Database [Video](https://youtu.be/GsSagoCByzc)
6) DB Crud Operations [Video](https://youtu.be/FV0hr-cw47A)
7) DB Join Operations [Video](https://youtu.be/-LqlkZ6S7p4)
8) RESTful Databases
    1) [Video 1](https://youtu.be/czJYswiRx-g)
    2) [Video 2](https://youtu.be/U73e3TJxvxM)
9) CSS
    1) [Intro Part 1](https://youtu.be/dSgJWh8vo1M)
    2) [Intro Part 2](https://youtu.be/6mdtAkrMKmw)
    3) [Intermediate Design](https://youtu.be/6D5sg7JdsZg)

## Overview

In this lab we will be adding object detection on top of the previous labs' functionality. At the end of this lab, you will be able to use your drone to detect objects as well as fly to both stationary and moving objects.

Here is a quick recap from the previous labs:

You built a web-based controller interface to control your drone that now works with MySQL databases. We now have three containers:

1. web-server (a web server in Python)
2. drone-controller (a Python program to talk to our drone API as well as newly added object detection logic)
3. mysql-db (a database server you talk to using MySQL)

We will be working with the same architecture in this lab with added functionality to the drone-controller container. Don't worry, knowledge of Machine Learning and Computer Vision is not a pre-requisite for this course!

The Object Detection section will give you an overview of what object detection is and how it has been implemented in the code that has been provided to you.

**IMPORTANT Note**

From Lab 5, we have seen multiple students having trouble with bringing up their Docker containers. Many of these problems were due to their Lab 4 containers/images remaining active resulting in port assignment conflicts. Also, be very careful with the name you give your database in the credentials.env file. It should match the database you're creating.

To avoid any hiccups for lab 6, we advise you to remove containers and images corresponding to previous labs using either Docker Desktop or these following commands in your terminal:

``` bash
  docker rm -f $(docker ps -a -q)
  docker rmi -f $(docker images -q)
  docker system prune -f --volumes
 ```

#### Credentials.env file...

As usual, you'll need to provide a `credentials.env` file that allows you to access the MySQL server in the Docker container. It's fine if you copy over the file from your last lab, but make sure to **update the database name**. Otherwise, create a new credentials.env file in the root of this directory and add the following 5 values. You will need to make up the last 3 fields:
```
  MYSQL_HOST=mysql-db
  MYSQL_DATABASE=lab6ece140a
  MYSQL_ROOT_PASSWORD= [...]
  MYSQL_USER= [...]
  MYSQL_PASSWORD= [...]
```

## Object Detection

Just as the title suggests, object detection is the technology that allows intelligent systems to detect the presence (and maybe even the location) of certain objects in a given image.

Some of the most well-known applications of object detection include autonomous driving, image annotation, and face recognition.

There are a variety of publicly-available algorithms to detect objects in images, with a wide range of approaches. We will be using a deep learning model called YOLO ([You Only Look Once](https://arxiv.org/abs/1506.02640)) that has focus on computational speed, even on large images.

Object detection can be broken down into two major segments: **image classification** and **object localization**.

Image Classification deals with the problem of predicting a label for a given image. For example, given any image of a water bottle, the algorithm must predict that this is an image of a "water bottle" and not some other object.

Object Localization deals with the problem of identifying the location of one or more objects in a given image. In the example of the water bottle, the algorithm must identify the coordinates of a box that surrounds the bottle.

YOLO is one of many algorithms that solves this problem. It uses a convolutional neural network architecture and can produce results in near real-time. This is the reason why it is very popular in real-time applications where prediction results need to be obtained quickly.

The list of objects that YOLO can detected can be found in `object_detection/coco.names`.

The image below shows the results of the YOLO model on a sample image.

![yolo_results](images/yolo.png)

### YOLO Implementation in Lab 6

The entire implementation of using YOLO to run inference (this is a term commonly used in Machine Learning to apply a trained model to a provided input) on an image and retrieving the results has been implemented for you in the `object_detection.py` file. Feel free to browse through it if you wish to extract out the functionality for your own projects.

Particularly, take a look at the `ImgProc.detect_object()` method. This function takes in an image and returns a tuple of two items. The first item (`detections`) is a tuple consisting of the names of the objects detected, the coordinates of the centers of the detected bounding boxes, and the bounding box coordinates and sizes respectively. The second item (`frame`) is a copy of the original image with the bounding boxes drawn onto it.

We are using OpenCV's `dnn` module to use a pre-trained YOLO model. Pre-trained simply means that the model has already been trained on a large dataset of objects and we can now directly apply this to detect objects. You are encouraged to go through the `ImgProc.detect_object()` code to understand how this has been implemented.

Now to tie this model implementation to our `drone-controller` container, take a look at the `process_image()` function in `command_dispatcher.py`. This function runs on a separate thread and continuously processes each frame retrieved from the drone at a certain interval. The variable `IMAGE_PROCESSING_DELAY` specifies this interval, which you can modify based on your computer's processing capabilities. This function calls the `ImgProc.detect_object()` method that we took a look at earlier. It then processes the object detection results. Pseudo code for this processing is provided below:

```python
"""
1. Send the retrieved frame (with bounding boxes drawn) to the web server via a POST request 
    i. This has been implemented in the send_frame() function already!
2. Continue if no objects were detected
3. Save the list of names of the detected objects to the global variable called objects_detected_names
4. If we are attempting to follow a specific object and if the target object has been detected:
    i. Retrieve the coordinate of the center of the detected object, and the bounding box information and call follow_object()   
"""
```

In challenge 2 and 3 (and extra credit), you will only have to be modifying the `follow_object()` function.

## Challenge 1 - Object Detection and UI Update

For this challenge, we will first be performing a series of four scans (with 90° rotation) of the room to maximize the variety in objects the drone can detect. This works best when the drone is at the center of your room. To achieve this, you will manually fly the drone (after takeoff) to an an approximate center of the room. You can alternatively position the drone in advance if your space is limited.

Since the drone does not have a compass onboard, we will be assigning pseudo directions relative to any one wall in your room. To do this, pick a wall in your room and stand facing this wall. You are now facing the "Front".  The remaining directions (Back, Left, and Right) will all be relative to this in the database.

Remember, the YOLO detection model returns the names of the objects detected and the coordinates of the corresponding bounding boxes. We have provided you with the code to read the object detection results and save it to the database.

### 1.1 Setup

In this first step, you will initiate the scan of the room. Start your Docker containers and go to the web controller. You will fly the drone to a center location of the room. You will then control the drone to turn in a series of 90° rotations, and capture an image of each direction in the room (front, back, left, right), using the "take snapshot" button while indicating which direction it was pointing at. Then the list of objects will be automatically populated into the `DetectedObjects` table in the Database.

### 1.2 Grab Images

Each time the `Detect Objects` button is pressed, it calls the `/snapshots` route in server.py, where it stores the current object detections in the current view, and images are automatically written into the `src/public` folder for you. Remember, objection detection is always running, so the snapshots route is just capture what was detected at the moment the button was pressed.

Your task is to retrieve the images from the public folder and display them on the webpage. The images are called "screenshot.jpg" and "detected_objects.jpg". **NOTE**: You may need to add a short delay either in server.py or web_ui.js so that the server has a moment to fully process and write the images to disk before returning control to the client.

Your task is to display updated versions of the images on your webpage (without a full page reload) each time you take a snapshot. Fortunately for you, this task can be accomplished in a couple of lines of JavaScript code. You'll add this code to the JavaScript file at: `server/src/public/web_ui.js`.

Remember that earlier in the quarter we repeatedly said that the browser is a great real-time rendering system?  Well, one thing your browser can do for you is automatically update images if it believes the images have changed (but you have to ask nicely). All you have to do is make it believe that the `src` property of the image has changed. Of course, it hasn't really (they are always named `screenshot.jpg` and `detected_objects.jpg`). There has to be a commmon technique to get the browser to automatically update an image without a full page reload! Try searching stackoverflow.com or use Google to see if you can find out how to do this task. The ability to find tips/tricks using these tools will be invaluable as an engineer (and this technique is pretty old and very common). It's only a few lines of code, so if you find some long, elaborate solution, you're probably taking the wrong approach.

### 1.3 Object List

The list of objects has been placed into the `DetectedObjects` table for you, so you will need to grab the list of objects and display it on the web page.

First, you will complete the implementation of `detection_data_route` in `server.py` to select the objects from the database and display them on the page. You can look at getting drone telemetry data from previous labs for inspiration. This implementation should look very similar.

This should should take place every time the `get snapshots` button is pressed since the detections will be updated in the database.

## Challenge 2 - Keep Object in Field of View

Now that we have detected objects, it's time to take our first step to achieving object following.

In this challenge, you will make use of the YOLO detection results to orient the drone such that a desired object is always within the drone's field of view (FOV). More specifically, the drone will rotate either clockwise or counter-clockwise to keep the center of the target object at approximately the center of the drone's FOV.

First, you will have to select an object to be your target. The list of objects that our YOLO model can recognize is listed in the `object_detection/coco.names` file. We have observed that YOLO performs better on larger objects, so you may want to start with those. You are free to select any object as your target, however you are encouraged to use larger objects like a backpack for better results.

**Make sure the target object is unique in the room. In other words, only have one instance of that object in the room so your algorithm does not get overwhelemed.**

### 2.1 Object Following Toggle Button

First, you will add a simple toggle to the webpage, which when clicked, will enable object follow mode. Note that the following two steps **2.2** and **2.3** must only be executed when this toggle button is enabled.

### 2.2 Rotation Angle Calculation

This is a simple math exercise. Given a point with coordinates (x, y), you have to determine an equation to calculate how much the drone must rotate such that the point now has coordinates (x', y) where x' is approximately at the center of the frame. Note that the altitude of the drone does not change (y is always the same).

**Hint**: The FOV of the DJI Tello drone we are working with is 82°.

### 2.3 Drone Rotation

You will now implement the equation from **2.2** in the `follow_object` function in `command_dispatcher.py`.
Details of the parameters passed into the function are provided in the function description. They are also listed below:

```python

def follow_object(coord, box):
    """
    :param coord: Coordinate (x, y) of the center of the target object
    :param box:   Coordinates of the bounding box of the target object in the form [x, y, w, h]
            x: x coordinate of the top-left coordinate of the box
            y: y coordinate of the top-left coordinate of the box
            w: width of the box
            h: height of the box
    """
```

To rotate the drone, you can directly call the `send_command()` function in `command_dispatcher.py` after computing the new coordinates. Parameters to this function follow the same format as the `send_command()` function in `server.py`. Be careful not to get the two functions mixed up.

## Challenge 3 - Fly to an Object

The next step is to be able to actually fly to the target object. In this challenge, the drone will fly to a stationary object and land close to it. Since we do not have a sensor to measure distance, we will approximate the distance between the drone and the target object using the area of the detected bounding box. Intuitively speaking, the larger the bounding box the closer the drone is to the object. This metric to estimate distance does not have a linear relationship with the actual distance between the drone and the object.

Note that this means larger objects will appear closer than smaller objects, so the image size constraint is only relative to the object itself. For example, if a water bottle and a chair are at approximately the same distance from the drone, the chair will appear to be closer than the water bottle if you tried to compare their sizes.

Having completed challenge 2, you can assume that the object is already at the center of the frame in follow object mode. All you have to do is calculate the distance to travel forward such that the target object is **within 50cm to the drone**.

Then, call `send_command()` similarly to Challenge 2 in `command_dispatcher.py` to make the drone actually fly towards the target object. Remember that the forward command argument to the drone is in meters! Add this code below your Challenge 2 implementation in the same `follow_object()` function.

## Extra Credit - Object Following

We will now make the drone be able to follow an object. You will be integrating everything you have learnt from the previous challenges for this challenge.

**Take Off and Follow**

You will start by sending commands to tell the drone to take off. Use the list of objects from Challenge 1 and click on an object you would like the drone to follow. Afterwards, you should pick the object up and walk around the room (while holding the object in your hand), and your drone should rotate and fly towards or away from the object in order to maintain a pre-defined distance form it. Note that this challenge is merely an extension of Challenge 2 and Challenge 3 to perform the action in real-time. You can implement this by using Challenge 2 and Challenge 3 and figuring out what you can do to make the drone follow the object even if the object is moving. 

A simple way to achieve this is to check if the object is still in the center of your view, if not move in the direction where it will be. BE CAREFUL! Try with small movements, so you don't over correct and visit your walls. The drone movements does not need to be super fast.

## Deliverables

Note: In the following screen recordings, show both your browser as well as the terminal running the code.

- A screen recording and a recording of the drone with your phone of Challenge 1: 40%
    - Drone flies to the center location of room if not already there
    - Take 4 snapshots of all 4 directions, be sure to show the 90 degree turns
    - Update the webpage on each new scan with the most recent pictures
    - Update object list based on the picture shown from the scan
- A screen recording and a recording of the drone with your phone of Challenge 2: 35%
    -  Show the toggle button for turning towards the object
    -  Show the drone turn towards the selected object
- A screen recording and a recording of the drone with your phone of Challenge 3: 20%
    -  Drone flies towards the selected object
- Extra Credit (both screen and drone recording is needed): (Points TBD)
    - Just show the drone rotating and flying toward the object
    - The object must be moving
- Github submission of your code 5%

## Due Date

Friday 3/12 11:59PM PST
