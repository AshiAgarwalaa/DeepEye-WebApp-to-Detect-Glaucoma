import os
from flask import Flask, url_for, redirect, render_template, request
from werkzeug import secure_filename

UPLOAD_FOLDER = 'C:/Users/ashi agarwal/Documents/Flask_apps/DeepEye/static/Images'

app=Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/instruction")
def instruction():
    return render_template("instructions.html")

@app.route("/projectDiscription")
def pro_dis():
    return render_template("projectDes.html")

@app.route("/tool")
def tool():
	return render_template("tool.html")

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
	return render_template("tool.html")


if __name__ == "__main__":
    app.run(debug=True)