# %pip install lxml

import requests
from lxml import html
import json
import time
import pandas as pd

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

newspapers_list = {
    "Los Andes" : ["https://www.losandes.com.ar/temas/mendoza", "https://www.losandes.com.ar/temas/mendoza/1", "https://www.losandes.com.ar/temas/mendoza/2"],
    "UNO" : ["https://www.diariouno.com.ar/politica"],
    "El Sol" : ["https://www.elsol.com.ar/mendoza/page/1/", "https://www.elsol.com.ar/mendoza/page/2/", "https://www.elsol.com.ar/mendoza/page/3/"],
    "MDZ" : ["https://www.mdzol.com/politica", "https://www.mdzol.com/politica/1", "https://www.mdzol.com/politica/2"]
}

json_news_list = {}

def get_tree(url):
    """Función auxiliar para obtener el árbol HTML de una URL"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Explicitly decode content as UTF-8 to handle special characters correctly
            return html.fromstring(response.content.decode('utf-8'))
    except Exception as e:
        print(f"Error cargando {url}: {e}")
    return None

def create_key_json(news_list, full_link, newspaper):
    """Función auxiliar para crear una clave en el JSON"""
    news_list[full_link] = {
        "new_headline": "",
        "new_summary": "",
        "new_body": "",
        "new_date" : "",
        "new_author": "",
        "newspaper": f"{newspaper}"
    }
    return news_list

def json_to_dataframe(news_list):
    """Función auxiliar para convertir el JSON a un DataFrame"""
    # Convertir el diccionario news_list en una lista de diccionarios para el DataFrame
    df_data = []
    for link, data in news_list.items():
        row = {"new_link": link} # La key principal (link) ahora es una columna
        row.update(data) # Agrega los demás campos (headline, summary, etc.)
        df_data.append(row)

    # Crear el DataFrame de pandas
    df_news = pd.DataFrame(df_data)
    return df_news

class scrapping_process:
    def __init__(self, newspaper, url_newspaper):
        self.newspaper = newspaper
        self.url_newspaper = url_newspaper
        print(f"scrapping_process instance created for {self.newspaper} ({self.url_newspaper})")

    def news_list_links(self, url, tree_main, news_list):
        if self.newspaper == "Los Andes":
            try:
                main_container = tree_main.xpath('/html/body/main/div[1]/div[1]')
            except Exception as e:
                print(f"Error obteniendo XPATH para 'main_container' en {url}: {e}")
                return None

            try:
                row_grouper_news = main_container[0].xpath('.//section[contains(@class, "grouper-simple-news") and contains(@class, "news-article-wrapper")]')
            except Exception as e:
                print(f"Error obteniendo XPATH para 'row_grouper_news' en {url}: {e}")
                return None

            for grouper in row_grouper_news:
                try:
                    cols_news = grouper.xpath('.//div[contains(@class, "col") and contains(@class, "col-lg-4")]')
                except Exception as e:
                    print(f"Error obteniendo XPATH para 'cols_news' en {url}: {e}")
                    return None

                for col in cols_news:
                    try:
                        full_link = col.xpath('.//a/@href')[0]
                    except Exception as e:
                        print(f"Error obteniendo XPATH para 'full_link' en {url}: {e}")
                        return None

                    if not full_link.startswith('http'): # Validar si el link es relativo o absoluto
                        full_link = f"https://www.losandes.com.ar{full_link}"
                    news_list = create_key_json(news_list, full_link, self.newspaper) # Inicializar estructura en el JSON
        else:
            print(f"No se encontró newspaper válido con '{self.newspaper}' ({url}).")

        return news_list

    def article_data(self, news_list, link, tree_article):
        if self.newspaper == "Los Andes":
            # Dirigete a full XPATH /html/body/main/div[2]/div[1]
            try:
                article_root = tree_article.xpath('/html/body/main/div[2]/div[1]')[0]
            except Exception as e:
                print(f"Error cargando 'article_root' de {link}:\n{e}")
                return None

            # Obten el string de /header/h1 -> "new_headline"
            try:
                headlines = article_root.xpath('./header/h1/text()')
                news_list[link]["new_headline"] = headlines[0].strip()
            except Exception as e:
                print(f"Error cargando 'new_headline' de {link}:\n{e}")

            # Obten el string de /div[1]/p -> "new_summary"
            try:
                topics_date = article_root.xpath('./div[1]/p//text()') # Usamos //text() para obtener texto incluso si está dentro de un <span> o <strong>
                news_list[link]["new_summary"] = " ".join(topics_date).strip()
            except Exception as e:
                print(f"Error cargando 'new_summary' de {link}:\n{e}")

            # Obten el string de /header/div/span -> "new_date"
            try:
                news_date_elements = article_root.xpath('./header/div/span/text()')
                news_list[link]["new_date"] = news_date_elements[0].strip()
            except Exception as e:
                print(f"Error cargando 'new_date' de {link}:\n{e}")

            # Obten el string de /div[3]/div[1]/div[1]/div/div[2]/div/div/a/b -> "new_author"
            try:
                author_elements = article_root.xpath('./div[3]/div[1]/div[1]/div/div[2]/div/div/a/b/text()')
                news_list[link]["new_author"] = author_elements[0].strip()
            except Exception as e:
                print(f"Error cargando 'new_author' de {link}:\n{e}")

            # Dirigete a /div[3] e itera en cada class que inicie con "article_body"
            try:
                body_divs = article_root.xpath('./div[3]')
                body_article_texts = body_divs[0].xpath('.//article[starts-with(@class, "article-body")]//text()')
                concatenated_text = " ".join([text.strip() for text in body_article_texts if text.strip()])
                news_list[link]["new_body"] = concatenated_text.strip()
            except Exception as e:
                print(f"Error cargando 'new_body' de {link}:\n{e}")

        else:
            print(f"No se encontró newspaper válido con '{self.newspaper}' ({link}).")

        return news_list

    def run(self, json_news_list):
        # 1. Se ingresa un newspaper, y se itera entre los links del json para obtener el acceso a cada noticia
        for url in self.url_newspaper:

            # 2. Obtenemos el HTML de la página
            try:
                tree_main = get_tree(url)
                time.sleep(1)
            except Exception as e:
                print(f"Error cargando {url}: {e}")
                continue

            # 3. Obtenemos los links de las noticias
            try:
                news_list = self.news_list_links(url, tree_main, {})
            except Exception as e:
                print(f"Error ejecutando función 'scrapping_process.news_list_links': {e}")
                continue

            # 4. paso extra: Chequeamos que esos links a noticias no esten cargados ya en la capa silver.
            # (A DESARROLLAR)

            # 5. Iteramos sobre las llaves del json 'new_list' para obtener los datos de cada noticia
            for link, data in news_list.items():
                try:
                    tree_article = get_tree(link)
                    time.sleep(1)
                except Exception as e:
                    print(f"Error cargando {link}:\n{e}")
                    continue
                try:
                    news_list = self.article_data(news_list, link, tree_article)
                except Exception as e:
                    print(f"Error ejecutando función 'scrapping_process.article_data': {e}")
                    continue

                json_news_list = {**json_news_list, **news_list}

        return json_news_list

if __name__ == "__main__":
    for newspaper, url_newspaper in newspapers_list.items():
        scrapping_instance = scrapping_process(newspaper, url_newspaper)
        json_news_list = scrapping_instance.run(json_news_list)
        time.sleep(1)

    df_news = json_to_dataframe(json_news_list)
    display(df_news)
    # df_news.to_csv("news_data.csv", index=False)