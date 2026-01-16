import requests
import json
import time

client_id = '2976654519207527' # Meta App > Configuración de la App > Básica > Identificador de la app
client_secret = '5c6d2c23580207a0a3c5db2f93f82b68' # Meta App > Configuración de la App > Básica > Clave secreta de la app

def meta_get_secret_token(scope="meta", key="access_token"):
    """
    Obtiene el Access Token del Secret AWS.
    """
    return dbutils.secrets.get(scope=scope, key=key)

def meta_check_token_expiry(secret_token, client_id, client_secret):
    """
    Verifica cuánto tiempo de uso le queda a un access token de Meta.
    Devuelve días restantes para la expiración.
    """
    debug_url = "https://graph.facebook.com/debug_token"
    app_token = f"{client_id}|{client_secret}"
    params = {
        'input_token': secret_token,
        'access_token': app_token
    }
    try:
        response = requests.get(debug_url, params=params)
        data = response.json()
        if response.status_code == 200 and 'data' in data:
            expires_at = data['data'].get('expires_at')
            if expires_at:
                now = int(time.time())
                seconds_left = expires_at - now
                days_left = seconds_left // 86400
                return days_left
            else:
                print("No se encontró información de expiración en la respuesta.")
                return None
        else:
            print(f"Error consultando el token: {data}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def meta_get_long_lived_token(client_id, client_secret, secret_token):
    """
    Intercambia un token (corto o largo) por uno nuevo de 60 días.
    Documentación: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived

    - Necesario: Haber almacenado un token como secret ni bien fue creado, verificar sus metadatos cada 7 días (o averiguar si se puede consultar expiración de un token), y cuando falte 8 días o menos, ejecutar esta función.
    - Debes: Almacenar este token como secret.
    """
    url = "https://graph.facebook.com/v21.0/oauth/access_token"

    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'fb_exchange_token': secret_token
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200 and 'access_token' in data:
            return data.get('access_token')
        else:
            print(f"❌ Error al canjear token: {data}")
            return None

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None
    
def meta_save_long_lived_token(access_token, scope="meta", key="access_token"):
    """
    Guarda el token en el secret AWS.
    """
    dbutils.secrets.put(scope=scope, key=key, value=access_token)

if __name__ == "__main__":

    # 1. Obtenemos el Access Token del Secret AWS
    secret_token = meta_get_secret_token(scope="meta", key="access_token")

    # 2. Verificamos si el Token tiene 8 días o menos para expirar 
    # if meta_check_token_expiry(secret_token, client_id, client_secret) <= 8:
    if meta_check_token_expiry(secret_token, client_id, client_secret) <= 60:

        # 3. Si tiene 8 días o menos para expirar, generamos un nuevo Access Token
        access_token = meta_get_long_lived_token(client_id, client_secret, secret_token)
        print(f"Nuevo Access Token: {access_token}")

        # 4. Guardamos el 'access_token' en el secret reemplazando el anterior
        meta_save_long_lived_token(access_token, scope="meta", key="access_token") 

    else:
        pass