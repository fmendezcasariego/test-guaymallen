import requests
import pandas as pd
import json
from datetime import datetime

class InstagramMetaClient:
    def __init__(self, access_token, instagram_account_id):
        self.access_token = access_token
        self.ig_id = instagram_account_id
        self.version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.version}"
        self.logs = []

    def _log_request(self, endpoint, params, response):
        """Registra los detalles de cada petición filtrando datos sensibles."""
        status_code = response.status_code
        
        # Clonamos parámetros para no modificar los originales y eliminamos el token
        safe_params = params.copy()
        if 'access_token' in safe_params:
            safe_params.pop('access_token')

        try:
            payload = response.json()
            # Si el status no es 200, Meta suele enviar el error en el payload
            raw_payload = json.dumps(payload)
        except Exception as e:
            raw_payload = f"Error parsing JSON: {str(e)} | Response Text: {response.text}"

        self.logs.append({
            "endpoint_called": endpoint,
            "parameters_used": json.dumps(safe_params),
            "raw_payload": raw_payload,
            "status_code": status_code,
            "extraction_timestamp": datetime.now(),
            "extraction_date": datetime.now().date()
        })

    def _make_request(self, path, params=None):
        """Manejador genérico de peticiones GET."""
        if params is None:
            params = {}
        params['access_token'] = self.access_token
        
        url = f"{self.base_url}/{path}"
        try:
            response = requests.get(url, params=params)
            self._log_request(path, params, response)
            return response.json()
        except Exception as e:
            # Manejo de errores de conexión (timeout, DNS, etc.)
            self.logs.append({
                "endpoint_called": path,
                "parameters_used": "Redacted (Error)",
                "raw_payload": f"Connection Error: {str(e)}",
                "status_code": 500,
                "extraction_timestamp": datetime.now(),
                "extraction_date": datetime.now().date()
            })
            return {"error": str(e)}

    def get_profile_stats(self):
        """1. ESTADÍSTICAS BÁSICAS DEL PERFIL"""
        fields = "name,username,biography,followers_count,follows_count,media_count,profile_picture_url"
        return self._make_request(f"{self.ig_id}", {"fields": fields})

    def get_profile_insights(self):
        """2. INSIGHTS DEL PERFIL (Rendimiento diario)"""
        metrics = "impressions,reach,profile_views,follower_count"
        return self._make_request(f"{self.ig_id}/insights", {"metric": metrics, "period": "day"})

    def get_audience_insights(self):
        """3. INSIGHTS DE AUDIENCIA (Demografía - Solo si > 100 seguidores)"""
        metrics = "audience_city,audience_country,audience_gender_age"
        return self._make_request(f"{self.ig_id}/insights", {"metric": metrics, "period": "lifetime"})

    def get_media_data(self):
        """4. DATOS DE PUBLICACIONES (Listado de Media)"""
        fields = "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count"
        return self._make_request(f"{self.ig_id}/media", {"fields": fields})

    def get_media_insights(self, media_id, media_type):
        """5. INSIGHTS DE PUBLICACIONES (Específicos por tipo)"""
        # Definición de métricas según documentación v21.0
        if media_type == 'VIDEO':
            metrics = "video_views,reach,saved,total_interactions"
        elif media_type == 'REELS':
            metrics = "plays,reach,saved,shares,total_interactions"
        else: # IMAGE o CAROUSEL_ALBUM
            metrics = "impressions,reach,saved,engagement"
            
        return self._make_request(f"{media_id}/insights", {"metric": metrics})

    def get_comments(self, media_id):
        """6. COMENTARIOS DE PUBLICACIONES"""
        fields = "id,text,timestamp,username,like_count"
        return self._make_request(f"{media_id}/comments", {"fields": fields})

    def get_mentions(self):
        """7. MENCIONES (Donde etiquetaron a la cuenta)"""
        fields = "id,caption,media_type,media_url,timestamp,owner"
        return self._make_request(f"{self.ig_id}/tags", {"fields": fields})

    def get_active_stories(self):
        """8. STORIES (Historias activas en las últimas 24h)"""
        stories = self._make_request(f"{self.ig_id}/stories", {"fields": "id,caption,media_type"})
        
        if 'data' in stories:
            for story in stories['data']:
                metrics = "exits,replies,taps_forward,taps_back,impressions,reach"
                self._make_request(f"{story['id']}/insights", {"metric": metrics})
        return stories

    def get_logs_dataframe(self):
        """Genera el DataFrame con el histórico de peticiones."""
        return pd.DataFrame(self.logs)
