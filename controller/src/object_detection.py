import numpy as np
import cv2
import time


class ImgProc():
  def __init__(self):
    # read pre-trained model and config file
    self.net = cv2.dnn.readNet("object_detection/yolov4-tiny.weights", "object_detection/yolov4-tiny.cfg")

    # read class names from text file
    self.classes = None
    with open("object_detection/coco.names", 'r') as f:
      self.classes = [line.strip() for line in f.readlines()]

    # generate different colors for different classes
    self.COLORS = np.random.uniform(0, 255, size=(len(self.classes), 3))

  # function to get the output layer names
  # in the architecture
  def get_output_layers(self, net):
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers

  # function to draw bounding box on the detected object with class name
  def draw_bounding_box(self, img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = str(self.classes[class_id])
    color = self.COLORS[class_id]
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

  def detect_objects(self, img):
    W = img.shape[1]
    H = img.shape[0]

    # create input blob
    sz = (416, 416)  # (224,224)
    normalization = 1.0 / 255.0
    blob = cv2.dnn.blobFromImage(img, normalization, sz, (0, 0, 0), True, crop=False)

    # set input blob for the network
    self.net.setInput(blob)

    # run inference through the network
    # and gather predictions from output layers
    outs = self.net.forward(self.get_output_layers(self.net))

    # initialization
    class_ids = []
    confidences = []
    boxes = []
    centroids = []
    conf_threshold = 0.3
    nms_threshold = 0.1

    # For each detetion from each output layer get the confidence, class id, bounding box params and ignore weak detections (confidence < 0.5)
    for out in outs:
      for detection in out:
        scores = detection[5:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]
        if confidence > conf_threshold:
          center_x = int(detection[0] * W)
          center_y = int(detection[1] * H)
          w = int(detection[2] * W)
          h = int(detection[3] * H)
          x = center_x - w / 2
          y = center_y - h / 2
          class_ids.append(class_id)
          confidences.append(float(confidence))
          boxes.append([x, y, w, h])
          centroids.append((center_x, center_y))

    # Apply non-max suppression to prevent duplicate detections
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    # Go through the detections remaining after NMS and draw bounding boxes
    detections = []
    frame = img.copy()
    for i in indices:
      i = i[0]
      box = boxes[i]
      x = box[0]
      y = box[1]
      w = box[2]
      h = box[3]
      self.draw_bounding_box(frame, class_ids[i], confidences[i], round(x), round(y), round(x + w), round(y + h))

      detections.append((self.classes[class_ids[i]], centroids[i], box))

    print("Detected Objects: ", detections)
    return detections, frame

if __name__ == "__main__":
  img = cv2.imread('sample_img.png')
  imgProc = ImgProc()
  imgProc.detect_objects(img)
