import os
import base64
import numpy as np
import io
from PIL import Image
from keras import backend as K
from skimage.measure import label,regionprops
import cv2
from skimage.transform import resize
from skimage.io import imsave
from keras.models import Model, load_model
from skimage.exposure import equalize_adapthist

from flask import Flask, url_for, redirect, render_template, request, jsonify
from werkzeug import secure_filename

UPLOAD_FOLDER = 'C:/Users/ashi agarwal/Documents/Flask_apps/DeepEye/static/Images'

app=Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app = Flask(__name__)

def get_od_model():
    global modelod
    modelod = load_model('Rimone_128.hdf5',custom_objects={'dice_coef':dice_coef,'iu':iu,'iouLoss':iouLoss,'acc':acc,'IOU':IOU})
    print('*OD Model loaded!!')
def get_oc_model():
    global modeloc
    modeloc = load_model('RIMONE_OC_model-ep027-loss0.389-val_loss0.394.hdf5',custom_objects={'dice_coef':dice_coef,'iu':iu,'iouLoss':iouLoss,'acc':acc,'IOU':IOU})
    print('*OC Model loaded!!')
#def get_class_model():
   # global model
   # model = load_model('Rimone_128.hdf5')
   # print('*OD Model loaded!!')
def preprocessOD():
    global image
    image=equalize_adapthist(np.array(Image.open('./static/Images/input.jpg').resize([128,128],Image.BICUBIC)))
    image=image.reshape([1,128,128,3])
    image/=np.max(image)
    image-=np.mean(image)
    image/=np.std(image)
    return image
def preprocessOC(image1):
    global mir,mic,mar,mac
    im=image1
    li=label(im+0.5)
    region=regionprops(li)
    mir,mic,mar,mac=region[0].bbox
    cx=image[0,mir:mar,mic:mac,:]
    c_x=cv2.resize(cx,(128,128),interpolation=cv2.INTER_AREA)
    c_x=c_x.reshape([1,128,128,3])
    return c_x
def dice_coef(y_true, y_pred):
    intersection = K.sum(y_true * y_pred)
    return (2. * intersection + 1) / (K.sum(y_true) + K.sum(y_pred) + 1)
#%%
def iu(y_true, y_pred):
    a2=K.sum(y_true*y_true)
    b2=K.sum(y_pred*y_pred)
    iu=K.sum(y_true*y_pred)/(a2+b2-K.sum(y_true*y_pred))
    return iu
#%%
def iouLoss(y_true, y_pred):
    return-K.log(iu(y_true,y_pred))
#%%
def acc(y_true, y_pred):
    TP = K.sum(y_true * y_pred)
    FP=K.sum((K.max(y_true)-y_true) * y_pred)
    return (TP)/(TP+FP)

#%%
def IOU(y_true, y_pred):
    intersection = K.sum(y_true * y_pred)
    union=K.sum((y_true+y_pred)/2)
    iou=intersection/union
    return iou

print("* Loading OD segmentation Model")
get_od_model()
print("* Loading OC segmentation Model")
get_oc_model()

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/instruction")
def instruction():
    return render_template("instructions.html")
@app.route("/publications")
def publications():
    return render_template("team.html")

@app.route("/projectDiscription")
def pro_dis():
    return render_template("projectDes.html")

@app.route("/tool")
@app.route("/tool/<od>/<status>/<oc>/<cdr>")
def tool(status=None,od=None,oc=None,cdr=None):
	return render_template("tool.html", var=status,od=od,oc=oc,cdr=cdr)

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.route("/upload",methods=['POST'])
def upload():
	if request.method == 'POST':
		file = request.files['file']
		filename = secure_filename(file.filename)
		os.remove('./static/Images/input.jpg')
		file.save('static/Images/input.jpg')
	    #return redirect(url_for('uploaded_file',filename=filename))
	    #return render_template("tool.html")
	return redirect(url_for('tool'))

@app.route("/preidct")
def predict():
    im1=preprocessOD()
    y_od=modelod.predict(im1, verbose=1)
    y_od=y_od.reshape([128,128])
    os.remove('./static/Images/od.jpg')
    imsave('./static/Images/od.jpg', y_od)
    im2=preprocessOC(y_od)
    y_oc=modeloc.predict(im2, verbose=1)
    y_oc=y_oc.reshape([128,128])
    oc_pred=np.zeros([128,128],dtype='float32')
    cx=cv2.resize(y_oc,((mac-mic),(mar-mir)),interpolation=cv2.INTER_AREA)
    oc_pred[mir:mar,mic:mac]=cx
    os.remove('./static/Images/oc.jpg')
    imsave('./static/Images/oc.jpg', oc_pred)
    li1=label(y_od+0.5)
    li2=label(oc_pred+0.5)
    region1=regionprops(li1)
    region2=regionprops(li2)
    mir1,mic1,mar1,mac1=region1[0].bbox
    mir2,mic2,mar2,mac2=region2[0].bbox
    OD_Diam=mac1-mic1
    OC_Diam=mac2-mic2
    CDR=OC_Diam/OD_Diam
    print(CDR)
    g_h= 1 if CDR>0.53 else 0
    if (g_h):
        response='   GLAUCOMATIC!'
        print(' *** GLAUCOMATIC!!! ***')
    else:
        response='   HEALTHY!'
        print(' *** HEALTHY!!! ***')

    return redirect(url_for('tool',status=response,od=str(OD_Diam), oc=str(OC_Diam),cdr=str(CDR-0.03)))

if __name__ == "__main__":
    app.run(debug=True)