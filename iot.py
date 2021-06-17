import face_recognition
import cv2
import datetime
import time
import numpy as np
import sys
import ibmiotf.application
import ibmiotf.device
import random
import ibm_boto3
from ibm_botocore.client import Config, ClientError

from cloudant.client import Cloudant
from cloudant.error import CloudantException 
from cloudant.result import Result, ResultByKey
#Provide your IBM Watson Device Credentials
organization = "5z48y5"
deviceType = "ESP32"
deviceId = "12345"
authMethod = "token"
authToken = "12345678"

def myCommandCallback(cmd):
        print("Command received: %s" % cmd.data)
        print(cmd.data['command'])
       
        if(cmd.data['command']=="open"):
                print("door open")
                
        if(cmd.data['command']=="close"):
                print("door close")
                

        if(cmd.data['command']=="lighton"):
                print("light on")
                
        if(cmd.data['command']=="lightoff"):
                print("light off")
               
        if(cmd.data['command']=="fanon"):
                print("fan on")
        if(cmd.data['command']=="fanoff"):
                print("fan off")
# This is a demo of running face recognition on live video from your webcam. It's a little more complicated than the
# other example, but it includes some basic performance tweaks to make things run a lot faster:
#   1. Process each video frame at 1/4 resolution (though still display it at full resolution)
#   2. Only detect faces in every other frame of video.

# PLEASE NOTE: This example requires OpenCV (the `cv2` library) to be installed only to read from your webcam.
# OpenCV is *not* required to use the face_recognition library. It's only required if you want to run this
# specific demo. If you have trouble installing it, try any of the other demos that don't require it instead.
try:
	deviceOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
	deviceCli = ibmiotf.device.Client(deviceOptions)
	#..............................................
	
except Exception as e:
	print("Caught exception connecting device: %s" % str(e))
	sys.exit()
deviceCli.connect()
# Get a reference to webcam #0 (the default one)
video_capture = cv2.VideoCapture(0)

COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "CxSLfU7ZsJlLsGML68optH1-lbCZmT3QEZISRNWERlJD" # eg "W00YiRnLW4a3fTjMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"
COS_RESOURCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/1d87764306ae4fe6b3f1f1894f21de93:9919fdb9-fafe-4bb3-9261-d0961faf0c9f::" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003abfb5d29761c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"


client = Cloudant("apikey-v2-1mx20vgbcub4ga86f7ue9wfwbo4u6gg7bvwbt60tsk9h", "2f29a39fffdd70ea15507a98b97b717e", url="https://apikey-v2-1mx20vgbcub4ga86f7ue9wfwbo4u6gg7bvwbt60tsk9h:2f29a39fffdd70ea15507a98b97b717e@ebc948ef-7e52-48b5-a89d-d08741e60f2a-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()
database_name = "vinaykumar31"

cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_RESOURCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)

# Load a sample picture and learn how to recognize it.
obama_image = face_recognition.load_image_file(r"Picture.jpeg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]

# Load a second sample picture and learn how to recognize it.
#biden_image = face_recognition.load_image_file(r"C:\Users\Kalkeseetharaman P K\Desktop\karan.jpg")
#biden_face_encoding = face_recognition.face_encodings(biden_image)[0]

'''biden_image1 = face_recognition.load_image_file("nikhil.jpeg")
biden_face_encoding1 = face_recognition.face_encodings(biden_image1)[0]'''

# Create arrays of known face encodings and their names
known_face_encodings = [
    obama_face_encoding
    #biden_face_encoding,
    #biden_face_encoding1
]
known_face_names = [
    "Vinay"
    #"Karan",
    #"Nikhil"
]

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            face_names.append(name)

    process_this_frame = not process_this_frame


    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
        picname=picname+".jpeg"
        pic=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
        cv2.imwrite(picname,frame)
        person=1
        my_database = client.create_database(database_name)        
        multi_part_upload("vinaykumar31",picname,pic+".jpeg")       
        if my_database.exists():
            print("'{database_name}' successfully created.")
            json_document = {
                    "_id": pic,
                    "link":COS_ENDPOINT+"/vinaykumar31/"+picname
                    }
            new_document = my_database.create_document(json_document)
            if new_document.exists():
                print("Document '{new_document}' successfully created.")
        time.sleep(1)
        t=34
        h=45
        data = {"d":{ 'temperature' : t, 'humidity': h, 'person': person}}
        #print data
        def myOnPublishCallback():
            print ("Published data to IBM Watson")

        success = deviceCli.publishEvent("Data", "json", data, qos=0, on_publish=myOnPublishCallback)
        if not success:
            print("Not connected to IoTF")
        time.sleep(1)
        deviceCli.commandCallback = myCommandCallback
        person=0
        
    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
deviceCli.disconnect()
# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()
