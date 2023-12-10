from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory, session, url_for
import requests
import os
import mercadopago
from flask import Flask, request, jsonify
from itsdangerous import URLSafeTimedSerializer as Serializer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave123'  # Cambia esto por una clave segura

# Simulación de almacenamiento de client_id y client_secret
clients = {
    os.environ.get('CLIENT_ID_USUARIOSAP', 'default_client_id'): {
        'client_secret': os.environ.get('CLIENT_SECRET_USUARIOSAP', 'default_client_secret')
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

    # Construir external_reference concatenando org_vta y uniqueid
    uniqueid = str(payload.get("uniqueid")) if payload.get("uniqueid") else ""
    external_reference = f"{org_vta}-{uniqueid}" if uniqueid else ""

    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": total_amount,
            }
        ],
        "notification_url": webhook_url,
        "external_reference": external_reference
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

        # Obtener el webhook_url dependiendo de org_vta
        org_vta = payload.get("org_vta")
        webhook_url = get_webhook_url(org_vta)

        if webhook_url is None:
            return jsonify({'error': 'No se encontró un webhook para este org_vta'}), 400

        # Enviar el webhook correspondiente
        payment_data = linkmp(payload, access_token, webhook_url)
        return jsonify(payment_data)
    except:
        return jsonify({'error': 'Token inválido'}), 401

def get_webhook_url(org_vta):
    # Definir aquí la lógica para obtener el webhook_url según org_vta
    if org_vta == "1000":
        return url_for('wh1000', _external=True)
    elif org_vta == "1020":
        return url_for('wh1020', _external=True)
    elif org_vta == "3000":
        return url_for('wh3000', _external=True)
    elif org_vta == "4000":
        return url_for('wh4000', _external=True)
    elif org_vta == "6000":
        return url_for('wh6000', _external=True)
    else:
        return None

# @app.route('/wh6000', methods=['POST'])
# def wh6000():
#     try:
#         # Verificar si la solicitud tiene un cuerpo JSON
#         if request.is_json:
#             data = request.json
#             # Imprimir el cuerpo del webhook en la terminal
#             print("Webhook Data:")
#             print(data)
            
#             # Obtener el ID del pago de la notificación
#             payment_id = data.get('data', {}).get('id')

#             if payment_id:
#                 # Realizar la solicitud GET a la API de MercadoPago para obtener información detallada
#                 api_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
#                 headers = {
#                     'Authorization': f'Bearer {os.environ.get('MERCADO_PAGO_BUPE_1C')}'
#                 }
#                 response = requests.get(api_url, headers=headers)

#                 if response.status_code == 200:
#                     payment_info = response.json()

#                     # Obtener la información necesaria
#                     external_reference = payment_info.get('external_reference', '')
#                     status = payment_info.get('status', '')
#                     status_detail = payment_info.get('status_detail', '')

#                     if status == 'approved' and status_detail == 'accredited':
#                         print(f"El ID {external_reference} fue aprobado y acreditado.")
#                     elif status == 'rejected' and status_detail == 'cc_rejected_bad_filled_security_code':
#                         print(f"El ID {external_reference} fue rechazado por código de seguridad incorrecto.")
#                     else:
#                         print(f"El ID {external_reference} tiene estado {status} y detalle {status_detail}.")
                    
#                     return jsonify({'status': 'ok'}), 200
#                 else:
#                     print(f"No se pudo obtener la información del pago. Código de estado: {response.status_code}")
#                     return jsonify({'error': 'No se pudo obtener la información del pago'}), 500
#             else:
#                 return jsonify({'error': 'ID de pago no proporcionado en la notificación'}), 400
#         else:
#             return jsonify({'error': 'La solicitud no contiene datos JSON'}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/wh4000', methods=['POST'])
# def wh4000():
#     try:
#         # Verificar si la solicitud tiene un cuerpo JSON
#         if request.is_json:
#             data = request.json
#             # Imprimir el cuerpo del webhook en la terminal
#             print("Webhook Data:")
#             print(data)
            
#             # Obtener el ID del pago de la notificación
#             payment_id = data.get('data', {}).get('id')

#             if payment_id:
#                 # Realizar la solicitud GET a la API de MercadoPago para obtener información detallada
#                 api_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
#                 headers = {
#                     'Authorization': f'Bearer {os.environ.get('MERCADO_PAGO_BUCL_1C')}'
#                 }
#                 response = requests.get(api_url, headers=headers)

#                 if response.status_code == 200:
#                     payment_info = response.json()

#                     # Obtener la información necesaria
#                     external_reference = payment_info.get('external_reference', '')
#                     status = payment_info.get('status', '')
#                     status_detail = payment_info.get('status_detail', '')

#                     if status == 'approved' and status_detail == 'accredited':
#                         print(f"El ID {external_reference} fue aprobado y acreditado.")
#                     elif status == 'rejected' and status_detail == 'cc_rejected_bad_filled_security_code':
#                         print(f"El ID {external_reference} fue rechazado por código de seguridad incorrecto.")
#                     else:
#                         print(f"El ID {external_reference} tiene estado {status} y detalle {status_detail}.")
                    
#                     return jsonify({'status': 'ok'}), 200
#                 else:
#                     print(f"No se pudo obtener la información del pago. Código de estado: {response.status_code}")
#                     return jsonify({'error': 'No se pudo obtener la información del pago'}), 500
#             else:
#                 return jsonify({'error': 'ID de pago no proporcionado en la notificación'}), 400
#         else:
#             return jsonify({'error': 'La solicitud no contiene datos JSON'}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/wh1020', methods=['POST'])
def wh1020():
    try:
        # Verificar si la solicitud tiene un cuerpo JSON
        if request.is_json:
            data = request.json
            # Imprimir el cuerpo del webhook en la terminal
            print("Webhook Data:")
            print(data)
            
            # Obtener el ID del pago de la notificación
            payment_id = data.get('data', {}).get('id')

            if payment_id:
                # Realizar la solicitud GET a la API de MercadoPago para obtener información detallada
                api_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
                headers = {
                    'Authorization': f'Bearer {os.environ.get("MERCADO_PAGO_ZJAR_1C")}'
                }
                response = requests.get(api_url, headers=headers)

                if response.status_code == 200:
                    payment_info = response.json()

                    # Obtener la información necesaria
                    external_reference = payment_info.get('external_reference', '')
                    status = payment_info.get('status', '')
                    status_detail = payment_info.get('status_detail', '')

                    if status == 'approved' and status_detail == 'accredited':
                        print(f"El ID {external_reference} fue aprobado y acreditado.")
                    elif status == 'rejected' and status_detail == 'cc_rejected_bad_filled_security_code':
                        print(f"El ID {external_reference} fue rechazado por código de seguridad incorrecto.")
                    else:
                        print(f"El ID {external_reference} tiene estado {status} y detalle {status_detail}.")
                    
                    return jsonify({'status': 'ok'}), 200
                else:
                    print(f"No se pudo obtener la información del pago. Código de estado: {response.status_code}")
                    return jsonify({'error': 'No se pudo obtener la información del pago'}), 500
            else:
                return jsonify({'error': 'ID de pago no proporcionado en la notificación'}), 400
        else:
            return jsonify({'error': 'La solicitud no contiene datos JSON'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/wh1000', methods=['POST'])
# def wh1000():
#     try:
#         # Verificar si la solicitud tiene un cuerpo JSON
#         if request.is_json:
#             data = request.json
#             # Imprimir el cuerpo del webhook en la terminal
#             print("Webhook Data:")
#             print(data)
            
#             # Obtener el ID del pago de la notificación
#             payment_id = data.get('data', {}).get('id')

#             if payment_id:
#                 # Realizar la solicitud GET a la API de MercadoPago para obtener información detallada
#                 api_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
#                 headers = {
#                     'Authorization': f'Bearer {os.environ.get('MERCADO_PAGO_BUAR_1C')}'
#                 }
#                 response = requests.get(api_url, headers=headers)

#                 if response.status_code == 200:
#                     payment_info = response.json()

#                     # Obtener la información necesaria
#                     external_reference = payment_info.get('external_reference', '')
#                     status = payment_info.get('status', '')
#                     status_detail = payment_info.get('status_detail', '')

#                     if status == 'approved' and status_detail == 'accredited':
#                         print(f"El ID {external_reference} fue aprobado y acreditado.")
#                     elif status == 'rejected' and status_detail == 'cc_rejected_bad_filled_security_code':
#                         print(f"El ID {external_reference} fue rechazado por código de seguridad incorrecto.")
#                     else:
#                         print(f"El ID {external_reference} tiene estado {status} y detalle {status_detail}.")
                    
#                     return jsonify({'status': 'ok'}), 200
#                 else:
#                     print(f"No se pudo obtener la información del pago. Código de estado: {response.status_code}")
#                     return jsonify({'error': 'No se pudo obtener la información del pago'}), 500
#             else:
#                 return jsonify({'error': 'ID de pago no proporcionado en la notificación'}), 400
#         else:
#             return jsonify({'error': 'La solicitud no contiene datos JSON'}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/wh3000', methods=['POST'])
# def wh3000():
#     try:
#         # Verificar si la solicitud tiene un cuerpo JSON
#         if request.is_json:
#             data = request.json
#             # Imprimir el cuerpo del webhook en la terminal
#             print("Webhook Data:")
#             print(data)
            
#             # Obtener el ID del pago de la notificación
#             payment_id = data.get('data', {}).get('id')

#             if payment_id:
#                 # Realizar la solicitud GET a la API de MercadoPago para obtener información detallada
#                 api_url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
#                 headers = {
#                     'Authorization': f'Bearer {os.environ.get('MERCADO_PAGO_BUMX_1C')}'
#                 }
#                 response = requests.get(api_url, headers=headers)

#                 if response.status_code == 200:
#                     payment_info = response.json()

#                     # Obtener la información necesaria
#                     external_reference = payment_info.get('external_reference', '')
#                     status = payment_info.get('status', '')
#                     status_detail = payment_info.get('status_detail', '')

#                     if status == 'approved' and status_detail == 'accredited':
#                         print(f"El ID {external_reference} fue aprobado y acreditado.")
#                     elif status == 'rejected' and status_detail == 'cc_rejected_bad_filled_security_code':
#                         print(f"El ID {external_reference} fue rechazado por código de seguridad incorrecto.")
#                     else:
#                         print(f"El ID {external_reference} tiene estado {status} y detalle {status_detail}.")
                    
#                     return jsonify({'status': 'ok'}), 200
#                 else:
#                     print(f"No se pudo obtener la información del pago. Código de estado: {response.status_code}")
#                     return jsonify({'error': 'No se pudo obtener la información del pago'}), 500
#             else:
#                 return jsonify({'error': 'ID de pago no proporcionado en la notificación'}), 400
#         else:
#             return jsonify({'error': 'La solicitud no contiene datos JSON'}), 400
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)