import os
import mercadopago
from flask import Flask, request, jsonify

app = Flask(__name__)

token_buar_1c = os.environ.get('MERCADO_PAGO_TEST_1C')
token_buar_3c = os.environ.get('MERCADO_PAGO_BUAR_3C')
token_zjar_1c = os.environ.get('MERCADO_PAGO_ZJAR_1C')
token_zjar_3c = os.environ.get('MERCADO_PAGO_ZJAR_3C')
token_bucl_1c = os.environ.get('MERCADO_PAGO_BUCL_1C')
token_bupe_1c = os.environ.get('MERCADO_PAGO_BUPE_1C')
token_bumx_1c = os.environ.get('MERCADO_PAGO_BUMX_1C')

tokens_mapping = {
    "1000": token_buar_1c,
    "1020": token_zjar_1c,
    "3000": token_bumx_1c,
    "4000": token_bucl_1c,
    "6000": token_bupe_1c
}

def linkmp(payload):
    org_vta = payload.get("org_vta")
    access_token = tokens_mapping.get(org_vta)

    if access_token is None:
        return {'error': 'No se encontró un token para este org_vta'}, 400

    sdk = mercadopago.SDK(access_token)
    title = str(payload.get("reference")) if payload.get("reference") else "Producto sin nombre"
    
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
        ]
    }

    preference_response = sdk.preference().create(preference_data)
    
    payment_link = preference_response['response'].get('init_point', '')

    if 'response' in preference_response and 'id' in preference_response['response']:
        preference_id = preference_response['response']['id']
        return {'preference_id': preference_id, 'enlace_de_pago': payment_link}
    else:
        return {'error': 'La respuesta no contiene el ID de preferencia', 'enlace_de_pago': payment_link}, 500

@app.route('/generar_link', methods=['POST'])
def generar_link():
    payload = request.get_json()

    if payload is None or 'org_vta' not in payload:
        return jsonify({'error': 'No se proporcionó un JSON válido o falta org_vta'}), 400

    # Convertir org_vta, totalAmount y reference a texto
    payload['org_vta'] = str(payload['org_vta'])
    payload['totalAmount'] = str(payload.get('totalAmount', ''))
    payload['reference'] = str(payload.get('reference', ''))

    payment_data = linkmp(payload)
    return jsonify(payment_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)