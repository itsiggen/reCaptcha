from flask import Flask, request
from flask_cors import CORS, cross_origin
from rest_framework import status
import logging

import json
import requests

app = Flask(__name__)
cors = CORS(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.config['CORS_HEADERS'] = 'Content-Type'

result = {}

@app.route("/alterego/event", methods=['POST','GET'])
@cross_origin()
def event():
    """
    Post a mouse or keyboard interaction events
    """
    
    #method is get
    if request.method == 'GET':
        return '', status.HTTP_200_OK

    #method is post
    else:
        try:
            event = json.loads(request.data)
            print(event);

            return {"success": True}
        except:
            return {"success": False}

# reCAPTCHA v2: "I am not a robot!" checkbox coordinates
@app.route("/alterego/recaptcha2_chkbox_coordinates", methods=['POST'])
@cross_origin()
def recaptcha2_chkbox_coordinates():

    try:
        coordinates = json.loads(request.data)
        print(coordinates)
        print("Coordinates checkbox: x=" + str(coordinates['x']) + ", y=" + str(coordinates['y']));
        
        return coordinates
    except:
        return {"success": False}


# reCAPTCHA v2: "I am not a robot!" checkbox
@app.route("/alterego/recaptcha2", methods=['POST'])
@cross_origin()
def recaptcha2():
    """
    Post reCAPTCHA v2 result
    """

    global result
    
    try:
        response = json.loads(request.data)
        
        payload = {
            "secret": "your_recaptcha_secret_key",
            "response": response
        }
        
        r = requests.post("https://www.google.com/recaptcha/api/siteverify", params=payload)

        result = r.json();
        print(result);
        
        return result
    except:
        return {"success": False}
    
@app.route("/alterego/result", methods=['GET'])
@cross_origin()
def recaptcha3_result():
    """
    Get reCAPTCHA v3 result
    """
    
    return result
    

# reCAPTCHA v3: score without user friction
@app.route("/alterego/recaptcha3", methods=['POST'])
@cross_origin()
def recaptcha3():
    """
    Post reCAPTCHA v3 result
    """
    
    global result

    try:
        response = json.loads(request.data)
        
        payload = {
            "secret": "your_recaptcha_secret_key",
            "response": response
        }

        r = requests.post("https://www.google.com/recaptcha/api/siteverify", params=payload)

        result = r.json();
        print(result);
        
        return result
    except:
        return {"success": False}


if __name__ == "__main__":
    app.run(debug=False)
