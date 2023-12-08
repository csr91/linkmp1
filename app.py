from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, session
import os
import mercadopago
from flask import Flask, request, jsonify
from itsdangerous import URLSafeTimedSerializer as Serializer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave123'  # Cambia esto por una clave segura

# Simulación de almacenamiento de client_id y client_secret
clients = {
    'usuariosap': {
        'client_secret': 'clavesap123'
    }
}

tokens_mapping = {
    "1000": os.environ.get('MERCADO_PAGO_BUAR_1C'),
    "1020": os.environ.get('MERCADO_PAGO_ZJAR_1C'),
    "3000": os.environ.get('MERCADO_PAGO_BUMX_1C'),
    "4000": os.environ.get('MERCADO_PAGO_BUCL_1C'),
    "6000": os.environ.get('MERCADO_PAGO_BUPE_1C')
}

def linkmp(payload, access_token, webhook_url):
    org_vta = payload.get("org_vta")
    access_token = tokens_mapping.get(org_vta)

    if access_token is None:
        return {'error': 'No se encontró un token para este org_vta'}, 400

    sdk = mercadopago.SDK(access_token)
    title = str(payload.get("reference")) if payload.get("reference") else "Producto. sin nombre"

    try:
        total_amount = float(payload.get("totalAmount")) if payload.get("totalAmount") else 0.0
    except ValueError:
        return {'error': 'El monto no es válido'}, 400

    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": total_amount,
            }
        ],
        "notification_url": webhook_url  # Agregar la URL del webhook aquí
    }

    preference_response = sdk.preference().create(preference_data)

    # Imprimir la respuesta de MercadoPago en la terminal
    print("Respuesta de MercadoPago:")
    print(preference_response)
    
    payment_link = preference_response['response'].get('init_point', '')

    if 'response' in preference_response and 'id' in preference_response['response']:
        preference_id = preference_response['response']['id']
        return {'preference_id': preference_id, 'enlace_de_pago': payment_link}
    else:
        return {'error': 'La respuesta no contiene el ID de preferencia', 'enlace_de_pago': payment_link}, 500


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    grant_type = request.args.get('grant_type')
    client_id = request.args.get('client_id')
    client_secret = request.args.get('client_secret')

    if grant_type != 'client_credentials':
        return jsonify({'error': 'El tipo de concesión debe ser client_credentials'}), 400

    if client_id not in clients or clients[client_id]['client_secret'] != client_secret:
        return jsonify({'error': 'Credenciales inválidas'}), 401

    s = Serializer(app.config['SECRET_KEY'])
    access_token = s.dumps({'client_id': client_id})
    print(f"Access Token: {access_token}")  # Imprimir el token generado
    return jsonify({'access_token': access_token})



@app.route('/generar_link', methods=['POST'])
def generar_link():
    access_token = request.headers.get('Authorization')

    if access_token is None or not access_token.startswith('Bearer '):
        return jsonify({'error': 'Token de autorización no válido'}), 401

    access_token = access_token.split('Bearer ')[1]  # Obtener el token

    s = Serializer(app.config['SECRET_KEY'])
    try:
        s.loads(access_token)
        payload = request.get_json()
        if payload is None or 'org_vta' not in payload:
            return jsonify({'error': 'No se proporcionó un JSON válido o falta org_vta'}), 400

        webhook_url = "https://linkmp1.vercel.app/webhook"  # Reemplaza con la URL de tu webhook
        payment_data = linkmp(payload, access_token, webhook_url)
        return jsonify(payment_data)
    except:
        return jsonify({'error': 'Token inválido'}), 401

    
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Verificar si la solicitud tiene un cuerpo JSON
        if request.is_json:
            data = request.json
            # Imprimir el cuerpo del webhook en la terminal
            print("Webhook Data:")
            print(data)
            # Aquí puedes agregar la lógica para procesar los datos del webhook según tus necesidades

            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'error': 'La solicitud no contiene datos JSON'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)