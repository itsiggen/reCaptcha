from flask import Flask, request
import logging
import json

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

result = {}

@app.route("/recaptcha/event", methods=['POST','GET'])
def event():
    """
    Post a mouse or keyboard interaction events
    """
    global result
    
    #method is get
    if request.method == 'GET':
        return result

    #method is post
    else:

        try:
            event = json.loads(request.data)
            result = json.dumps(event, sort_keys=True)
            
            print(result)

            return {"success": True}
        except:
            return {"success": False}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)  