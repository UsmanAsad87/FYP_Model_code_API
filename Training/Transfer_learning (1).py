from os import path
import numpy as np
import pandas as pd
from tqdm import tqdm
import pickle

from deepface.basemodels import  ArcFace
from deepface.commons import functions

import tensorflow as tf
def transfer_learning():
    batch_size = 32
    img_height = 112
    img_width = 112
    data_dir ='data_FYP_clean'
    train_ds = tf.keras.utils.image_dataset_from_directory(
                data_dir,
                validation_split=0.2,
                subset="training",
                seed=123,
                image_size=(img_height, img_width),
                )
    val_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            validation_split=0.2,
            subset="validation",
            seed=123,
            image_size=(img_height, img_width),
            batch_size=batch_size)
    
    
    # tf.expand_dims(val_ds,0)
    # train_ds = functions.normalize_input(train_ds,'ArcFace')
    # val_ds = functions.normalize_input(val_ds,'ArcFace')
    train_images=[]
    for image_batch, labels_batch in train_ds:
        # image_batch=tf.expand_dims(image_batch,0)
        train_images.append(image_batch[0])
    val_images=[]
    for image_batch, labels_batch in val_ds:
        # image_batch=tf.expand_dims(image_batch,0)
        val_images.append(image_batch[0])
        



    base_model=ArcFace.loadModel()
    print(base_model.summary())
    base_model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])
    base_model.fit(train_images,validation_data=val_images,epochs=20)


transfer_learning()