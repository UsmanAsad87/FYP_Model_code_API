from os import path
from deepface.basemodels import  ArcFace
import tensorflow as tf
from tensorflow.keras.models import *
from tensorflow.keras.layers import *
from keras.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt
import pickle

from math import pi


class ArcLoss(tf.keras.losses.Loss):


    def __init__(self, margin=0.5, scale=64, name="arcloss"):
        super().__init__(name=name)
        self.margin = margin
        self.scale = scale
        self.threshold = tf.math.cos(pi - margin)
        self.cos_m = tf.math.cos(margin)
        self.sin_m = tf.math.sin(margin)
        self.safe_margin = self.sin_m * margin

    @tf.function
    def call(self, y_true, y_pred):

        # Calculate the cosine value of theta + margin.
        cos_t = y_pred
        sin_t = tf.math.sqrt(1 - tf.math.square(cos_t))

        cos_t_margin = tf.where(cos_t > self.threshold,
                                cos_t * self.cos_m - sin_t * self.sin_m,
                                cos_t - self.safe_margin)

        # The labels here had already been onehot encoded.
        mask = y_true
        cos_t_onehot = cos_t * mask
        cos_t_margin_onehot = cos_t_margin * mask

        # Calculate the final scaled logits.
        logits = (cos_t + cos_t_margin_onehot - cos_t_onehot) * self.scale

        losses = tf.nn.softmax_cross_entropy_with_logits(y_true, logits)

        return losses

    def get_config(self):
        config = super(ArcLoss, self).get_config()
        config.update({"margin": self.margin, "scale": self.scale})
        return config

def transfer_learning():
    batch_size = 32
    img_height = 112
    img_width = 112
    data_dir ='dataset_FYP_clean'
    train_ds = tf.keras.utils.image_dataset_from_directory(
                data_dir,
                validation_split=0.2,
                subset="training",
                seed=123,
                image_size=(img_height, img_width),
                label_mode='categorical'
                )
    val_ds = tf.keras.utils.image_dataset_from_directory(
            data_dir,
            validation_split=0.2,
            subset="validation",
            seed=123,
            image_size=(img_height, img_width),
            batch_size=batch_size,
            label_mode='categorical')
    base_model=ArcFace.loadModel()
    # print(model.summary())

    # model = Model(base_model.input, base_model.layers[-7].output)
    model = Model(base_model.input, base_model.output)
    # print(model.summary())
    for layer in model.layers:
        layer.trainable=True
    model.layers[-2].trainable = True
    model.layers[-3].trainable = True
    model.layers[-4].trainable = True
    model.layers[-5].trainable = True
    model.layers[-6].trainable = True
    model.layers[-7].trainable = True
    model.layers[-8].trainable = True
    model.layers[-9].trainable = True
    model.layers[-10].trainable = True
    model.layers[-1].trainable = True
    new_model= Sequential()
    #new_model.add(Input(shape=(112,112,3)))
    new_model.add(model)
    new_model.add(Flatten())
    new_model.add(Dropout(0.5))
    new_model.add(Dense(256,activation='relu'))
    new_model.add(Dropout(0.2))
    new_model.add(Dense(151,activation='softmax'))
    new_model.summary()


    # # new_model.load_weights('saved_model_5/my_model_weights.h5')
    # # print('usman loaded')
    

    new_model.compile(
        loss=ArcLoss(),# 'categorical_crossentropy', #ArcLoss(),#
              optimizer='adam',
              metrics=['accuracy'])

    
    # # loss, acc = new_model.evaluate(val_ds,verbose=1)
    # # print("Untrained model, accuracy: {:5.2f}%".format(100 * acc))

    cp1= ModelCheckpoint(filepath='saved_model8', monitor='loss',     save_best_only=True, verbose=1, mode='min')
    callbacks_list = [cp1]

    # # print('here2')
    hist=new_model.fit(train_ds,validation_data=val_ds,epochs=100, callbacks=callbacks_list)
    print('HISTORY::')
    print(hist.history)

    # json_string = model.to_json()
    # json_string
    #new_model.save_weights('Saved_model/my_model_weights.h5')
    new_model.save_weights('saved_model8/my_model_weights.h5')
    # new_model.save_model('saved_model8/my_model.h5')
    new_model.save('saved_model8/my_model.h5')


    # with open('/trainHistoryDict', 'wb') as file_pi:
    #     pickle.dump(hist.history, file_pi)
    # with open('/trainHistoryDict', "rb") as file_pi:
    #     history = pickle.load(file_pi)


    plt.plot(hist.history['accuracy'])
    plt.plot(hist.history['val_accuracy'])
    plt.title('Model accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Test'], loc='upper left')
    plt.show()

    plt.plot(hist.history['loss'])
    plt.plot(hist.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Test'], loc='upper left')
    plt.show()
    
transfer_learning()