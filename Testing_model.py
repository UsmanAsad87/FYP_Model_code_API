from flask import Flask, render_template, Response, request
import requests
import cv2
import datetime, time
import os, sys
import numpy as np
import base64
from threading import Thread
import argparse



import os
# rootdir = 'D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/Faces/'
# rootdir = 'D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/data_FYP_clean2/'
# rootdir = 'D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/data_FYP_clean2/extra/'
rootdir ='D:/FYP_code/FYP_Model_code_API/dataset_small_facenet_4id/'
# rootdir ='/home/all/FYP_Model_code_API/EXTRA/'

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        print(subdir)
        print(file)
        # print(img)
        try:
            imgPath=os.path.join(subdir, file)
            # imgPath='EXTRA/data_FYP_clean2/Aamir_Khan/'+file
            # imgPath=subdir+'/'+file
            print(imgPath)
            # # if(imgPath=='D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/data_FYP_clean\Aishwarya_Rai\6.jpg'):
            # my_img = cv2.imread(imgPath, cv2.IMREAD_UNCHANGED)
            # b64 = base64.b64encode(my_img) 
            # img = "data:image/jpeg;base64," + b64.decode('utf-8')

            img=''
            with open(imgPath, "rb") as img_file:
                my_string = base64.b64encode(img_file.read())
                img = "data:image/jpeg;base64," + my_string.decode('utf-8') # b64.decode('utf-8')
                # print(img)


            # api_url = "http://172.30.34.64:5000/findface"
            api_url = "http://10.25.28.127:5000/findface"
            # api_url = "http://192.168.0.100:5000/findface"
            # print(api_url)
            
            data= {
                    "model_name": "ArcFace",
                    "location":"lab ICV",
                    "img":img
            }
            # print(data)
            response = requests.post(api_url, json=data,)
            print(response.json())


        except Exception as e:
            print(e)
            continue

        

        # cv2.imshow('image', my_img)
        # k = cv2.waitKey(0) & 0xFF
        # # wait for ESC key to exit
        # if k == 27:
        #     cv2.destroyAllWindows()


        print("========\n\n")      
        # time.sleep(0.2)


# try:
#     # if(imgPath=='D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/data_FYP_clean\Aishwarya_Rai\6.jpg'):
#     # my_img = cv2.imread('D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/data_FYP_clean/Aishwarya_Rai/6.jpg', cv2.IMREAD_UNCHANGED)
#     # b64 = base64.b64encode(my_img) 
#     # img = "data:image/jpeg;base64," + b64.decode('utf-8')
#     img=''
#     with open("D:/FYP_code/FYP_MODEL_CODE_API/EXTRA/data_FYP_clean/Aishwarya_Rai/6.jpg", "rb") as img_file:
#         my_string = base64.b64encode(img_file.read())
#         img = "data:image/jpeg;base64," + my_string.decode('utf-8') # b64.decode('utf-8')

    
#     # api_url = "http://172.30.34.64:5000/findface"
#     api_url = "http://127.0.0.1:5000/findface"
#     # print(api_url)
    
#     data= {
#             "model_name": "ArcFace",
#             "location":"lab ICV",
#             "img":img
#     }

#     # with open("example.txt", "w") as f:
#     #     f.write(img)
#     response = requests.post(api_url, json=data,)
#     print(response.json())
#     print("========\n\n")  


# except Exception as e:
#     print(e)