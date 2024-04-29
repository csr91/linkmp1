from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/hola')
def hola():
    return 'hola'
    
# URI de conexión a MongoDB
uri = "mongodb+srv://cesarmendoza77:7hLCBopqFoTBmF4v@cluster0.papc1wn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Crear un nuevo cliente y conectar al servidor
client = MongoClient(uri, server_api=ServerApi('1'))

# Enviar un ping para confirmar una conexión exitosa
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

if __name__ == '__main__':
    app.run(debug=True)