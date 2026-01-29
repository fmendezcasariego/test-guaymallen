import requests
import pandas as pd
import json
from datetime import datetime
import time

class InstagramMetaClient:
    def __init__(self, access_token, instagram_account_id):
        self.access_token = access_token
        self.ig_id = instagram_account_id
        self.version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.version}"
        self.logs = []

    def _scrub(self, text):
        if not text or not isinstance(text, str): return text
        return text.replace(self.access_token, "REDACTED_TOKEN")

    def _log_step(self, endpoint, params, response, page_num):
        try:
            res_json = response.json()
            payload = self._scrub(json.dumps(res_json))
        except:
            payload = self._scrub(response.text)

        safe_params = params.copy() if isinstance(params, dict) else {"url": self._scrub(str(params))}
        if 'access_token' in safe_params: safe_params.pop('access_token')

        self.logs.append({
            "endpoint_called": endpoint,
            "parameters_used": json.dumps(safe_params),
            "raw_payload": payload,
            "status_code": response.status_code,
            "extraction_timestamp": datetime.now(),
            "extraction_date": datetime.now().date(),
            "payload_page": page_num
        })

    def _request(self, path, params=None, page_num=0):
        url = path if path.startswith("http") else f"{self.base_url}/{path}"
        if "access_token" not in url:
            if params is None: params = {}
            params['access_token'] = self.access_token
        try:
            response = requests.get(url, params=params)
            self._log_step(path.split('?')[0], params, response, page_num)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def _get_paginated_data(self, path, params):
        all_data = []
        page_num = 0
        response = self._request(path, params, page_num)
        all_data.append(response)
        while response and "paging" in response and "next" in response["paging"]:
            page_num += 1
            response = self._request(response["paging"]["next"], page_num=page_num)
            all_data.append(response)
        return all_data

    def get_profile_stats(self):
        fields = "id,ig_id,name,username,biography,followers_count,follows_count,media_count,profile_picture_url,website"
        return self._request(f"{self.ig_id}", {"fields": fields})

    def get_profile_insights(self):
        metrics = "impressions,reach,profile_views,follower_count,email_contacts,get_directions_clicks,text_message_clicks,website_clicks"
        return self._request(f"{self.ig_id}/insights", {"metric": metrics, "period": "day"})

    def get_audience_insights(self):
        metrics = "audience_city,audience_country,audience_gender_age,audience_locale"
        return self._request(f"{self.ig_id}/insights", {"metric": metrics, "period": "lifetime"})

    def get_media_data(self):
        fields = "id,caption,comments_count,is_comment_enabled,is_shared_to_feed,like_count,media_product_type,media_type,media_url,permalink,shortcode,thumbnail_url,timestamp,username"
        return self._get_paginated_data(f"{self.ig_id}/media", {"fields": fields})

    def get_media_insights(self, item):
        media_id = item.get('id')
        media_type = item.get('media_type')
        media_product_type = item.get('media_product_type', 'FEED')
        if media_product_type in ["REELS", "CLIPS"]:
            metrics = "clips_replays_count,comments,likes,plays,reach,saved,shares,total_interactions"
        elif media_type == "VIDEO":
            metrics = "video_views,reach,saved,total_interactions"
        else:
            metrics = "impressions,reach,saved,engagement"
        return self._request(f"{media_id}/insights", {"metric": metrics})

    def get_comments(self, media_id):
        fields = "id,text,timestamp,username,like_count,from,parent_id"
        return self._get_paginated_data(f"{media_id}/comments", {"fields": fields})

    def get_mentions(self):
        fields = "id,caption,media_type,media_url,permalink,timestamp,username"
        return self._get_paginated_data(f"{self.ig_id}/tags", {"fields": fields})

    def get_active_stories(self):
        """CORREGIDO: Usa 'navigation' en lugar de exits/taps."""
        fields = "id,caption,media_product_type,media_type,media_url,permalink,timestamp"
        stories_pages = self._get_paginated_data(f"{self.ig_id}/stories", {"fields": fields})
        # for page in stories_pages:
        #     if "data" in page:
        #         for story in page["data"]:
        #             # Métricas actualizadas según error v21.0
        #             metrics = "impressions,reach,replies,saved,shares,navigation"
        #             self._request(f"{story['id']}/insights", {"metric": metrics})
        return stories_pages

    def export_logs(self):
        return pd.DataFrame(self.logs)
