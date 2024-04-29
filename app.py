from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/hola')
def hola():
    return 'hola'
    
if __name__ == '__main__':
    app.run(debug=True)