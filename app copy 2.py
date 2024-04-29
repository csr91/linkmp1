from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/hola')
def hola():
    return 'hola'

@app.route('/api/carrito', methods=['POST'])
def escribir_carrito(client, userid, avisos, action):
    try:
        # Selecciona la base de datos y la colección
        db = client['cannubis']
        collection = db['carritos']
        
        # Busca si ya existe un carrito con el userid dado
        existing_cart = collection.find_one({"userid": userid})
        
        if existing_cart:
            print("Se encontró un carrito existente para el userid:", userid)
            print("Contenido del carrito existente:")
            print(existing_cart)
            
            if action == "paste":
                # Verificar si avisoid ya existe en el carrito
                for aviso in avisos:
                    avisoid = aviso["avisoid"]
                    cant = aviso["cant"]
                    precio = aviso["precio"]
                    
                    existing_aviso = next((item for item in existing_cart["avisos"] if item["avisoid"] == avisoid), None)
                    
                    if existing_aviso:
                        # Si el aviso ya existe, sumar la cantidad actual con la cantidad del POST
                        existing_aviso["cant"] += cant
                        existing_aviso["precio"] = precio
                        print(f"Cantidad y precio del aviso '{avisoid}' actualizados en el carrito.")
                    else:
                        existing_cart["avisos"].append(aviso)
                        print(f"Aviso con avisoid '{avisoid}' añadido al carrito.")
                
                # Actualizar el carrito en la colección
                collection.update_one({"userid": userid}, {"$set": {"avisos": existing_cart["avisos"]}})
                
            elif action == "calc":
                # Verificar si avisoid ya existe en el carrito y la cantidad actual es 1
                for aviso in avisos:
                    avisoid = aviso["avisoid"]
                    cant = aviso["cant"]
                    
                    existing_aviso = next((item for item in existing_cart["avisos"] if item["avisoid"] == avisoid), None)
                    
                    if existing_aviso:
                        if existing_aviso["cant"] == 1 and cant == -1:
                            return jsonify({"error": f"No se puede reducir la cantidad del aviso '{avisoid}' a menos de 1."}), 400
                        else:
                            existing_aviso["cant"] += cant
                            print(f"Cantidad del aviso '{avisoid}' actualizada en el carrito.")
                    else:
                        print(f"No se encontró el aviso '{avisoid}' en el carrito.")
                
                # Actualizar el carrito en la colección
                collection.update_one({"userid": userid}, {"$set": {"avisos": existing_cart["avisos"]}})
            
            elif action == "delete":
                # Eliminar el aviso del carrito si existe
                for aviso in avisos:
                    avisoid = aviso["avisoid"]
                    
                    existing_aviso = next((item for item in existing_cart["avisos"] if item["avisoid"] == avisoid), None)
                    
                    if existing_aviso:
                        existing_cart["avisos"].remove(existing_aviso)
                        print(f"Aviso con avisoid '{avisoid}' eliminado del carrito.")
                    else:
                        print(f"No se encontró el aviso '{avisoid}' en el carrito.")
                
                # Actualizar el carrito en la colección
                collection.update_one({"userid": userid}, {"$set": {"avisos": existing_cart["avisos"]}})
                
        else:
            if action == "paste":
                print("Crear nuevo carrito")
                # Crear un nuevo carrito con los datos proporcionados
                nuevo_carrito = {
                    "userid": userid,
                    "avisos": avisos
                }
                # Insertar el nuevo carrito en la colección
                collection.insert_one(nuevo_carrito)
                print("Nuevo carrito creado")
            else:
                print("La acción no es 'paste', no se creará un nuevo carrito.")
        
    except Exception as e:
        print("Error al escribir en el carrito:", e)

@app.route('/api/carrito', methods=['GET'])
def obtener_carrito(client, userid):
    try:
        # Selecciona la base de datos y la colección
        db = client['cannubis']
        collection = db['carritos']
        
        # Busca el carrito del usuario
        existing_cart = collection.find_one({"userid": userid})
        
        # Convertir ObjectId a cadena
        if existing_cart:
            existing_cart['_id'] = str(existing_cart['_id'])
        
        return existing_cart
        
    except Exception as e:
        print("Error al obtener el carrito:", e)
        return None

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