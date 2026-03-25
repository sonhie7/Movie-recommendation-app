import requests

TMDB_API_KEY = "ad693879a3cd48522828018f13ab69a1"

def get_movie_poster(title):
    try:
        # 🔥 1. Clean title (remove year)
        clean_title = title.split("(")[0].strip()

        # 🔥 2. First search
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={clean_title}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if "results" in data and data["results"]:
            for movie in data["results"]:
                poster_path = movie.get("poster_path")
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"

        # 🔥 3. Second try (replace special characters)
        alt_title = clean_title.replace("'", "").replace(":", "")
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={alt_title}"
        response = requests.get(url, timeout=5)
        data = response.json()

        if "results" in data and data["results"]:
            poster_path = data["results"][0].get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"

    except Exception as e:
        print("TMDb error:", e)

    return None