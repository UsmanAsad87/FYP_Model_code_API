import warnings
warnings.filterwarnings("ignore")
#new push
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

#------------------------------

from flask import Flask, jsonify, request, make_response,render_template,redirect


import argparse
import uuid
import json
import time
from tqdm import tqdm
import matplotlib.image
import pandas as pd
import pickle
from deepface.commons import functions
from deepface.detectors import FaceDetector
import pymongo
import base64
import numpy as np
from datetime import datetime
from numba import cuda

# from mtcnn.mtcnn import MTCNN
import cv2
# detector =MTCNN()



from flask import redirect,url_for ,render_template



#------------------------------

import tensorflow as tf
tf_version = int(tf.__version__.split(".")[0])

#------------------------------

if tf_version == 2:
	import logging
	tf.get_logger().setLevel(logging.ERROR)

#------------------------------

from deepface import DeepFace

#------------------------------

import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
  # Restrict TensorFlow to only allocate memory on the first GPU
  try:
    tf.config.experimental.set_visible_devices(gpus[0], 'GPU')
    tf.config.experimental.set_memory_growth(gpus[0], True)
    print("GPU memory growth enabled")
  except RuntimeError as e:
    # Visible devices must be set before GPUs have been initialized
    print(e)




class User:
	def __init__(self, id,recentTime,recentLocation, timeStamps, imgUrl):
		self.id = id
		self.recentLocation = recentLocation
		self.timeStamps= timeStamps
		self.imgUrl = imgUrl
		self.recentTime = recentTime

	def __init__(self, item):
		self.id = item['name']
		self.recentLocation ='' if "none" in item['recent_location'] else item['recent_location']
		self.timeStamps= item['timeStamps']
		self.imgUrl ="data:image/png;base64,"+ item["imgUrl"]
		self.recentTime = '' if item['recent_timeStamp']==datetime.min else item['recent_timeStamp'].strftime("%m/%d/%Y, %H:%M:%S")

	def __init__(self, item,stamps):
		self.id = item['name']
		self.recentLocation ='' if "none" in item['recent_location'] else item['recent_location']
		self.timeStamps= stamps
		self.imgUrl ="data:image/png;base64,"+ item["imgUrl"]
		self.recentTime = '' if item['recent_timeStamp']==datetime.min else item['recent_timeStamp'].strftime("%m/%d/%Y, %H:%M:%S")

class TimeStamp:
	def __init__(self,time,location,img):
		self.time = time
		self.location= location
		self.img = img

	def __init__(self, stamp):
		self.time = stamp['time'].strftime("%m/%d/%Y, %H:%M:%S")
		self.location= stamp['location']
		self.img = stamp["img"]




app = Flask(__name__)
# app.config['MONGO_URI']="mongodb://localhost:27017/FaceRecog"
# mongo=PyMongo(app)

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

# mydb = myclient["FaceRecog"]
mydb = myclient["FaceRecog"]

collection=mydb["Users"]

#------------------------------

if tf_version == 1:
	graph = tf.get_default_graph()

#------------------------------
#Service API Interface
@app.route('/',methods=['GET','POST'])
def view():
	#Search User
	if request.method=='POST':
		#If it is search by name
		if request.form.get('name') != None:
			name=request.form['name']
			return searchByName(name=name)

		#else search By image
		searchImg = request.files['newcomer']
		return searchByImg(img=searchImg)


	#If you want to get all users	
	return getAllUser()
	# allDocs=collection.find({}).sort('recent_timeStamp',-1)
	# Docs=[]
	# for item in allDocs:
	# 	stamps=[]
	# 	for st in item['timeStamps']:
	# 		stamp=TimeStamp(st)
	# 		stamps.append(stamp)
	# 	doc=User(item,stamps)
	# 	Docs.append(doc)
	# return render_template('index.html',allTodo=Docs,pic=doc.imgUrl)

@app.route('/details/<string:id>',methods=['GET','POST'])
def details(id):
	user=collection.find_one({"name":id})
	stamps=[]
	for item in user['timeStamps']:
		stamp=TimeStamp(item)
		stamps.append(stamp)
		# print("DATA: "+stamp.location+" "+stamp.time+" "+stamp.img+"  ")
	stamps=sorted(stamps,key= lambda x: x.time,reverse=True)
	userData= User(user,stamps)
	# for st in userData.timeStamps:
	# 	print(st.time)
	return render_template('details.html',user=userData)

@app.route('/findface', methods=['POST'])
def findface():

	global graph

	tic = time.time()
	req = request.get_json()
	trx_id = uuid.uuid4()

	resp_obj = jsonify({'success': False})

	if tf_version == 1:
		with graph.as_default():
			resp_obj = findfaceWrapper(req, trx_id)
	elif tf_version == 2:
		resp_obj = findfaceWrapper(req, trx_id)

	#--------------------------

	toc =  time.time()
	print("TOTAL TIME:"+str(toc-tic))

	resp_obj["trx_id"] = trx_id
	resp_obj["seconds"] = toc-tic

	return resp_obj, 200

@app.route('/test')
def test():
	resp_obj = jsonify({'success': True})
	return resp_obj, 200

def getAllUser():
	allDocs=collection.find({}).sort('recent_timeStamp',-1)
	Docs=[]
	for item in allDocs:
		stamps=[]
		for st in item['timeStamps']:
			stamp=TimeStamp(st)
			stamps.append(stamp)
		doc=User(item,stamps)
		Docs.append(doc)
	return render_template('index.html',allTodo=Docs,pic=doc.imgUrl)

def searchByImg(img):
	if img.filename=='':
		return getAllUser()

	filename=img.filename.split(".")
	name=filename[0]
	ext=filename[1]
	img_bytes = img.read()
	encoded_string = base64.b64encode(img_bytes)
	str_encoded_string=str(encoded_string)
	str_encoded_string=str_encoded_string[2:]
	instance='data:image/'+ext+';base64,'+str_encoded_string
	instance=instance[:-1]
	resultDf=pd.DataFrame()
	try:
		resultDf = DeepFace.find(instance
		, db_path = 'dataset_small'
		, model_name = 'ArcFace'
		, distance_metric = 'cosine'
		, detector_backend = 'mtcnn'
		, silent=True
	)
	except Exception as err:
		resp_obj = jsonify({'success': False, 'error': str(err)}), 205
	
	if resultDf.empty:
		print("Not found")
		return render_template('index.html',allTodo=[])
	else:
		print(resultDf)
		Docs=[]	
		IDs=[]
		for index, row in resultDf.iterrows():
			imgurl=row['identity']
			imgurl= imgurl.replace("\\", "/")
			id=imgurl.split("/")[1]
			if row["ArcFace_cosine"] < 0.56 and not id in IDs:
				imgurl=row['identity']
				#print(imgurl.split("/")[1] in IDs)
				user=collection.find_one({"name":id})
				IDs.append(id)
				print(id)
				#print(user==None)
				#if no user is found then this will run
				if(user==None):
					print("none")
					return render_template('index.html',allTodo=Docs)

				
				
				stamps=[]
				for item in user['timeStamps']:
					stamp=TimeStamp(item)
					stamps.append(stamp)

				userData= User(user,stamps)
				Docs.append(userData)



       
		print(Docs)
		return render_template('index.html',allTodo=Docs)


			# imgurl=topMatchDf['identity'][0]
			# imgurl= imgurl.replace("\\", "/")
			# ID=imgurl.split("/")
			# user=collection.find_one({"name":ID[1]})
			# print(user==None)
			# #if no user is found then this will run
			# if(user==None):
			# 	return render_template('index.html',allTodo=[])

			
			
			# stamps=[]
			# for item in user['timeStamps']:
			# 	stamp=TimeStamp(item)
			# 	stamps.append(stamp)
			# 	print("DATA: "+stamp.location+" "+stamp.time+"  ")
			# userData= User(user,stamps)
			# Docs.append(userData)
		
		return render_template('index.html',allTodo=Docs)


		#WORKING
		# print(resultDf)
		# print(resultDf['identity'][0])
		# topMatchDf=resultDf.nsmallest(1, 'ArcFace_cosine')
		# imgurl=topMatchDf['identity'][0]
		# imgurl= imgurl.replace("\\", "/")
		# ID=imgurl.split("/")
		# user=collection.find_one({"name":ID[1]})
		# print(user==None)
		# #if no user is found then this will run
		# if(user==None):
		# 	return render_template('index.html',allTodo=[])

		# #if user record is found	
		# Docs=[]	
		# stamps=[]
		# for item in user['timeStamps']:
		# 	stamp=TimeStamp(item)
		# 	stamps.append(stamp)
		# 	print("DATA: "+stamp.location+" "+stamp.time+"  ")
		# userData= User(user,stamps)
		# Docs.append(userData)
		# for st in userData.timeStamps:
		# 	print(st.time)
		# return render_template('index.html',allTodo=Docs)

def searchByName(name):
	#if search query is empty
	if(name==''):
		return getAllUser()
	
	#if no user is found then this will run
	user=collection.find_one({"name":name})
	if(user==None):
		return render_template('index.html',allTodo=[])

	#if user record is found	
	Docs=[]	
	stamps=[]
	for item in user['timeStamps']:
		stamp=TimeStamp(item)
		stamps.append(stamp)
		print("DATA: "+stamp.location+" "+stamp.time+"  ")
	userData= User(user,stamps)
	Docs.append(userData)
	for st in userData.timeStamps:
		print(st.time)
	return render_template('index.html',allTodo=Docs)





# # @app.route('/view')
# # def view():
# # 	allDocs=collection.find({},{"name":1,"_id":0,'recent_location':1,'recent_timeStamp':1,'timeStamps':1}).sort('recent_timeStamp',-1).limit(2)
# # 	for item in allDocs:
# # 		#print(item)
# # 		print("DATA:")
# # 		print(item['name'])
# # 		print(item['recent_location'])
# # 		a=item['recent_timeStamp']
# # 		print("year =", a.year)
# # 		print("month =", a.month)
# # 		print("day =", a.day)
# # 		print("hour =", a.hour)
# # 		print("minute =", a.minute)
# # 		for stamps in item['timeStamps']: 
# # 			print(stamps)
# # 			m=stamps['time']
# # 			print("year =", m.year)
# # 			print("month =", m.month)
# # 			print("day =", m.day)
# # 			print("hour =", m.hour)
# # 			print("minute =", m.minute)
		

# 	# for item in allDocs:
# 	# 	if  not ('none' in item["recent_timeStamp"]):
# 	# 		print(item)
# 	# for item in allDocs:
# 	# 	if 'none' in item["recent_timeStamp"]:
# 	# 		print(item)
# 	return '<h1>Welcome to our face recognizer!</h1>'
# # @app.route('/1')
# # def welcome1():
# #     return render_template('index.html')





def loadBase64Img(uri):
   encoded_data = uri.split(',')[1]
   nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
   return img

# Using Retina face
def extract_face(image, resize=(224, 224)):
	tic1 =  time.time()
	# faces = detector.detect_faces(image)
	detector_backend = 'retinaface'
	face_detector = FaceDetector.build_model(detector_backend)
	faces = FaceDetector.detect_faces(face_detector, detector_backend, image, align = False)
	toc1 =  time.time()
	print("Extract onlt time MTCNN:"+str(toc1-tic1))

	facesInb64=[]
	for face, (x, y, w, h) in faces:
		face_boundary = image[int(y):int(y+h), int(x):int(x+w)]
		face_image=cv2.resize(face_boundary,resize)
		res, frame = cv2.imencode('.jpg', face_image)   
		b64 = base64.b64encode(frame) 
		img = "data:image/jpeg;base64," + b64.decode('utf-8')
		facesInb64.append(img)
	# for face in faces:
	# 	x1, y1, width, height = face['box']
	# 	x2, y2 = x1 + width, y1 + height
	# 	face_boundary = image[y1:y2, x1:x2]
	# 	face_image=cv2.resize(face_boundary,resize)

	# 	res, frame = cv2.imencode('.jpg', face_image)   
	# 	b64 = base64.b64encode(frame) 
	# 	img = "data:image/jpeg;base64," + b64.decode('utf-8')
	# 	facesInb64.append(img)

	return facesInb64

#///Using MTCNN
# def extract_face(image, resize=(224, 224)):
# 	tic1 =  time.time()
# 	# faces = detector.detect_faces(image)
# 	print("Extract onlt time MTCNN:"+str(toc1-tic1))
# 	for face in faces:
# 		x1, y1, width, height = face['box']
# 		x2, y2 = x1 + width, y1 + height
# 		face_boundary = image[y1:y2, x1:x2]
# 		face_image=cv2.resize(face_boundary,resize)

# 		res, frame = cv2.imencode('.jpg', face_image)   
# 		b64 = base64.b64encode(frame) 
# 		img = "data:image/jpeg;base64," + b64.decode('utf-8')
# 		facesInb64.append(img)

# 	return facesInb64


# @cuda.jit
# def subFunction_kernel(face_img, db_path, model_name, distance_metric, detector_backend, resp_obj):
#     # Perform the computation on a single element of the input array
# 	try:
# 		tic3 =  time.time()

# 		resultDf = DeepFace.find(face_img
# 			, db_path = "dataset_small"
# 			, model_name = model_name
# 			, distance_metric = distance_metric
# 			, detector_backend = detector_backend
# 			, silent=True
# 		)

# 		toc3 =  time.time()
# 		print("FIND_FACE TIME:"+str(toc3-tic3))

# 	except Exception as err:
# 		print("Exception: ",str(err))
# 		resp_obj = jsonify({'success': False, 'error': str(err)}), 205

# 	#-------------------------------------

# 	tic4 =  time.time()
# 	resp_obj = {}
# 	if not resultDf.empty:
# 		print(resultDf)
# 		resp_obj['face_found']= 'True'
# 		topMatchDf=resultDf.nsmallest(1, 'ArcFace_cosine')
# 		imgurl=topMatchDf['identity'][0]
# 		print(topMatchDf['ArcFace_cosine'][0])
# 		if(topMatchDf['ArcFace_cosine'][0] <0.56):
# 			resp_obj['imgurl']= imgurl
# 			addTimeStampOfUser(imgurl=imgurl,location=location,img=face_img)


# 	toc4 =  time.time()
# 	print("POST Processing TIME:"+str(toc4-tic4))

# 	if resultDf.empty or topMatchDf['ArcFace_cosine'][0] >0.56:
# 		resp_obj['face_found']= 'False'
# 		resp_obj['imgurl']= 'None'
# 		try:	
# 			# face = DeepFace.detectFace2(face_img)
# 			face=True
# 			if(face):
# 				resp_obj['HasFace']= face
# 				resp_obj['face_found']= 'true'
# 				faceImg = DeepFace.detectFace(img_path = face_img, target_size=(224, 224), enforce_detection = False, detector_backend = 'mtcnn', align = True)
# 				count=fcount('dataset_small/')
# 				newpath = 'dataset_small/ID'+str(count)  
# 				if not os.path.exists(newpath):
# 					os.makedirs(newpath)

# 				save_path='dataset_small/ID'+str(count)+'/image'+str(count)+'.png'
# 				resp_obj['imgurl']= save_path
# 				matplotlib.image.imsave(save_path, faceImg)
# 				resp_obj['faceAdded']= 'true'

# 				#for updating the embeddings
# 				file_name="representations_arcface.pkl"
# 				db_path='dataset_small'
# 				f = open(db_path+'/'+file_name, 'rb')
# 				representations = pickle.load(f)
# 				# img_path="dataset_small/ID10/image10.png"
# 				rep= DeepFace.represent(save_path,model_name="ArcFace",detector_backend = 'mtcnn')
# 				instance=[]
# 				instance.append(save_path)
# 				instance.append(rep)
# 				representations.append(instance)
# 				f = open(db_path+'/'+file_name, "wb")
# 				pickle.dump(representations, f)
# 				f.close()
# 				ID=save_path.split("/")
# 				print(ID[1])
				
# 				now=datetime.now()
# 				#location="lab"
# 				timeStamp={"time":now,"location":location,"img":face_img}

# 				with open(save_path, "rb") as img_file:
# 					my_string = base64.b64encode(img_file.read())

# 				rec={"name":ID[1],"imgUrl":my_string.decode("utf-8"),"timeStamps":[timeStamp,],'recent_timeStamp':now,'recent_location':location}
# 				collection.insert_one(rec)

# 			else:
# 				resp_obj['HasFace']= face

# 		except Exception as err:
# 			print("Exception: ",str(err))
# 			resp_obj = jsonify({'success': False, 'error': str(err)}), 205
			
# 		return resp_obj

# 	# resp_obj["resultDf"] = resultDf.to_json()
# 	return resp_obj




@cuda.jit
def subFunction_kernel(face_img, db_path, model_name, distance_metric, detector_backend, resp_obj):
    # Perform the computation on a single element of the input array
	resp_obj['sdfs']='dfsd'

	# resp_obj["resultDf"] = resultDf.to_json()
	return resp_obj


# @cuda.jit
@cuda.jit
def parallelForLoop(
    face_imgs, db_path, model_name, distance_metric, detector_backend, resp_all
):

    # Get the index of the current thread
    i = cuda.grid(1)

    # Iterate over the face images and process them in object mode
    while i < len(face_imgs):
        face_img = face_imgs[i]
        # CUDA kernel code here, using object mode as needed
        i += cuda.gridDim.x * cuda.blockDim.x
        resp_obj = {"imgurl": None, "face_found": "false"}
        subFunction_kernel(
            face_img, db_path, model_name, distance_metric, detector_backend, resp_obj
        )
        resp_all["resp" + str(len(face_img))] = resp_obj

    # Iterate over the input array in parallel
	# i = cuda.grid(1)
    # if i < len(face_imgs):
    #     face_img = face_imgs[i]
    #     resp_obj = {'imgurl': None, 'face_found': 'false'}
    #     subFunction_kernel(face_img, db_path, model_name, distance_metric, detector_backend, resp_obj)
    #     resp_all['resp' + str(len(face_img))] = resp_obj


def parallelize(face_imgs, db_path, model_name, distance_metric, detector_backend):
    # Allocate memory on the GPU
    d_face_imgs = cuda.to_device(face_imgs)
    d_resp_all = cuda.to_device({})

    # Define the number of threads per block
    threads_per_block = 256

    # Calculate the number of blocks needed based on the input data size
    blocks_per_grid = (len(face_imgs) + threads_per_block - 1) // threads_per_block

    # Launch the kernel function with the specified number of blocks and threads
    parallelForLoop[blocks_per_grid, threads_per_block](d_face_imgs, db_path, model_name, distance_metric, detector_backend, d_resp_all)

    # Copy the results back to the host
    resp_all = d_resp_all.copy_to_host()

    return resp_all

def findfaceWrapper(req, trx_id = 0):

	resp_obj = jsonify({'success': False})

	#-------------------------------------
	#find out model

	model_name = "ArcFace"; distance_metric = "cosine"; detector_backend = 'retinaface'; location='unknown'

	if "model_name" in list(req.keys()):
		model_name = req["model_name"]
	
	if "location" in list(req.keys()):
		location= req["location"]

	if "detector_backend" in list(req.keys()):
		detector_backend = req["detector_backend"]

	#-------------------------------------
	#retrieve images from request

	img = ""
	if "img" in list(req.keys()):
		img = req["img"] #list
		#print("img: ", img)

	validate_img = False
	if len(img) > 11 and img[0:11] == "data:image/":
		validate_img = True

	if validate_img != True:
		print("invalid image passed!")
		return jsonify({'success': False, 'error': 'you must pass img as base64 encoded string'}), 205

#add for loop to iterate for searching the faces and call the below code on it
	#-------------------------------------
	#call represent function from the interface

 

    
	resultDf=pd.DataFrame()

	#Just to check

	tic1 =  time.time()
	img2=loadBase64Img(img)
	toc1 =  time.time()
	print("loadBase64Img TIME:"+str(toc1-tic1))
	resp_all={}
	
	tic2 = time.time()
	face_imgs=extract_face(img2)
	toc2 = time.time()
	print("extract_faces TIME:"+str(toc2-tic2))



	parallelize(face_imgs, "dataset_small" , model_name, distance_metric, detector_backend)






		


	if(len(face_imgs)==0):
		resp_all['face_found']= 'False'
	
	
	return resp_all

def fcount(path):
    count1 = 0
    for root, dirs, files in os.walk(path):
            count1 += len(dirs)
    return count1

def addAllUserInDb(path):
	dir_list = os.listdir(path)
	for item in dir_list:
		if os.path.isdir(os.path.join(path, item)):
			filename=os.listdir(os.path.join(path, item))
			imgpath=os.path.join(path, item,filename[0])
			with open(imgpath, "rb") as img_file:
				my_string = base64.b64encode(img_file.read())
			rec={"name":item,"imgUrl":my_string.decode("utf-8"),"recent_timeStamp":datetime.min,'recent_location':'none',"timeStamps":[]}
			collection.insert_one(rec)

def addTimeStampOfUser(imgurl,location,img):
	imgurl= imgurl.replace("\\", "/")
	ID=imgurl.split("/")
	#print(imgurl)
	#print(ID[1])
	print(ID[1])
	one=collection.find_one({"name":ID[1]})
	# print(one)
	timeStamps=one["timeStamps"]
	now=datetime.now()
	#location="lab"
	# print(now)
	
	timeStamp={"time":now,"location":location,'img':img}
	timeStamps.append(timeStamp)
	# print(timeStamp)
	prev={"name":ID[1]}
	nextt={"$set":{"timeStamps":timeStamps,"recent_timeStamp":now,'recent_location':location}}
	up=collection.update_many(prev,nextt)
	print(up.modified_count)

def resetMongoDb():
	# dictionary={"name":"usman","marks":20}
	# collection.insert_one(dictionary)
	# collection.delete_many({})
	# addAllUserInDb('dataset_small')
	collection.delete_one({"name":"ID13"})

if __name__ == '__main__':
	resetMongoDb()
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-p', '--port',
		type=int,
		default=5000,
		help='Port of serving api')
	args = parser.parse_args()

	#app.run(host='0.0.0.0', port=80,debug=False)
	app.run(host='0.0.0.0', port=args.port,debug=True,threaded=True)
	# app.run(host='192.168.0.104', port=5000,debug=False)
	# app.run(host='0.0.0.0', port=args.port,debug=True)

	# app.run( port=args.port,debug=True)




