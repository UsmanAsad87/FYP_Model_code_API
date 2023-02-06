from os import path
from deepface.basemodels import  ArcFace
import tensorflow as tf
from tensorflow.keras.models import *
from tensorflow.keras.layers import *
from keras.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt

from math import pi


model =ArcFace.loadModel()
model.summary()