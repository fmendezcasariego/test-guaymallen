import requests
import json
import os

secret_token = ''

API_VERSION = 'v21.0'
base_url = f"https://graph.facebook.com/{API_VERSION}/"

APP_ID = '2976654519207527' # Meta App > Configuración de la App > Básica > Identificador de la app
APP_SECRET = '5c6d2c23580207a0a3c5db2f93f82b68' # Meta App > Configuración de la App > Básica > Clave secreta de la app

ig_user_id = '17841401240132992'  # Empieza con 1784...

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
            return data
        else:
            print(f"❌ Error al canjear token: {data}")
            return None

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None
    
def meta_ig_get_user_profile(secret_token, base_url, ig_user_id):
    """Obtiene información básica del perfil y conteo de seguidores"""
    url = f"{base_url}{ig_user_id}"
    params = {
        'fields': 'username,name,biography,followers_count,follows_count,media_count,profile_picture_url',
        'access_token': secret_token
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error obteniendo perfil: {response.status_code}")
        print(response.text)
        return None

def meta_ig_get_user_media(secret_token, base_url, ig_user_id, limit=5):
    """Obtiene los últimos posts con sus métricas básicas"""
    url = f"{base_url}{ig_user_id}/media"

    # Campos que queremos de cada post
    fields = 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count'

    params = {
        'fields': fields,
        'access_token': secret_token,
        'limit': limit
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error obteniendo posts: {response.status_code}")
        return None

def meta_ig_get_media_comments(secret_token, base_url, ig_user_id, media_id):
    """Obtiene los comentarios de un post"""
    url = f"{base_url}{media_id}/comments"
    params = {
        'fields': 'id,text,timestamp',
        'access_token': secret_token
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error obteniendo comentarios: {response.status_code}")
        return None
    
def meta_ig_get_media_insights(secret_token, base_url, ig_user_id, media_id):
    """Obtiene métricas de un post"""
    url = f"{base_url}{media_id}/insights"
    params = {
        'metric': 'engagement,impressions,saved,reach,reach_by_country,video_views',
        'access_token': secret_token
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error obteniendo métricas: {response.status_code}")
        return None
    
def meta_ig_complete_process():
    print("--- 1. Obteniendo Perfil ---")
    perfil = meta_ig_get_user_profile(secret_token, base_url, ig_user_id)
    if perfil:
        print(f"Usuario: {perfil.get('username')}")
        print(f"Seguidores: {perfil.get('followers_count')}")
        print("-" * 30)

    print("\n--- 2. Obteniendo Últimos Posts ---")
    posts = meta_ig_get_user_media(secret_token, base_url, ig_user_id, limit=1000) # Traemos todo
    # posts = get_user_media(limit=3) # Traemos los últimos 3

    print(f"\n{posts['paging']}\n")

    if posts and 'data' in posts:
        orden = 1
        for post in posts['data']:
            print(f"\n{post}\n")
            # print("\n----- " + "Post " + str(orden) + " -----" )
            # print(f"Fecha: {post.get('timestamp')}")
            # print(f"Likes: {post.get('like_count')} | Comentarios: {post.get('comments_count')}")
            # print(f"Caption: {post.get('caption', 'Sin descripción')}")
            # print(f"Link: {post.get('permalink')}")
            # orden = 1 + orden
        print("\n--------------------")

if __name__ == "__main__":
    meta_ig_complete_process()


