import requests

OMDB_API_KEY = "abf9abb9"  # Remplace par ta clé API OMDb

def get_movie_details(title):
    """
    Retourne les infos d'un film depuis OMDb
    :param title: titre du film
    :return: dictionnaire avec Poster, Plot, Year, Genre, Actors
    """
    # Utiliser le paramètre 't' pour le titre
    url = f"http://www.omdbapi.com/?t={requests.utils.quote(title)}&apikey={OMDB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return {
                    "Title": data.get("Title"),
                    "Year": data.get("Year"),
                    "Plot": data.get("Plot"),
                    "Poster": data.get("Poster"),
                    "Genre": data.get("Genre"),
                    "Actors": data.get("Actors")
                }
            else:
                print(f"OMDb API error: {data.get('Error', 'Unknown error')}")
    except Exception as e:
        print(f"Erreur lors de la requête OMDb: {e}")
    return {}
