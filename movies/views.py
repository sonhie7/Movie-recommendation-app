from django.shortcuts import render, redirect
from django.contrib import messages
from conn.test_snowflake import movies, load_data,get_connection, get_all_users, add_rating, get_user_ratings, get_watchlist, add_to_watchlist, remove_from_watchlist, is_in_watchlist, get_user_rating, validate_user_login
from conn.recommender import recommend_movies
from conn.omdb import get_movie_details
from django.core.paginator import Paginator
from conn.omdb import get_movie_details
from conn.tmdb import get_movie_poster
from conn.recommender import recommend_similar_movies




def home(request):
    # =========================
    # 📊 LOAD DATA
    # =========================
    movies_df, ratings, users, watchlist = load_data()

    user_id = request.session.get('user_id')
    user_ratings = {}
    in_watchlist = {}

    # =========================
    # 👤 USER DATA
    # =========================
    if user_id:
        user_ratings_data = get_user_ratings(user_id)

        for _, row in user_ratings_data.iterrows():
            user_ratings[row['MOVIE_ID']] = row['RATINGS']

        watchlist_movies = get_watchlist(user_id)
        in_watchlist = {m['MOVIE_ID']: True for m in watchlist_movies}

    # =========================
    # 🔍 SEARCH
    # =========================
    query = request.GET.get("q")
    if query:
        movies_df = movies_df[movies_df["TITLE"].str.contains(query, case=False, na=False)]

    # =========================
    # 🎭 GENRE FILTER
    # =========================
    genre = request.GET.get("genre")
    if genre and genre in movies_df.columns:
        movies_df = movies_df[movies_df[genre] == 1]

    # =========================
    # 🔽 SORTING
    # =========================
    sort = request.GET.get("sort")

    if sort == "az":
        movies_df = movies_df.sort_values(by="TITLE")

    elif sort == "year":
        movies_df = movies_df.sort_values(by="RELEASE_DATE", ascending=False)

    elif sort == "rating":
        avg_ratings = ratings.groupby("MOVIE_ID")["RATINGS"].mean()
        movies_df = movies_df.merge(avg_ratings, on="MOVIE_ID", how="left")
        movies_df = movies_df.sort_values(by="RATINGS", ascending=False)

    # =========================
    # 📄 PAGINATION (AFTER FILTERS ✅)
    # =========================
    movies_list = movies_df.to_dict("records")

    paginator = Paginator(movies_list, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # =========================
    # 🎬 ADD POSTERS (ONLY CURRENT PAGE ✅)
    # =========================
    enriched_movies = []

    for movie in page_obj:
        movie["Poster"] = get_movie_poster(movie["TITLE"])
        enriched_movies.append(movie)

    page_obj.object_list = enriched_movies

    # =========================
    # 🎯 RETURN
    # =========================
    return render(request, "home.html", {
        "movies": page_obj,
        "page_obj": page_obj,
        "user_ratings": user_ratings,
        "in_watchlist": in_watchlist,
        "user_id": user_id
    })


def movie_detail(request, movie_id):
    genre_columns = [
        'ACTION','ADVENTURE','ANIMATION','CHILDREN','COMEDY','CRIME',
        'DOCUMENTARY','DRAMA','FANTASY','FILM_NOIR','HORROR','MUSICAL',
        'MYSTERY','ROMANCE','SCI_FI','THRILLER','WAR','WESTERN'
    ]

    # Get data
    movies, ratings, users, watchlist = load_data()

    # Filter movie
    filtered = movies[movies["MOVIE_ID"] == int(movie_id)]
    if filtered.empty:
        return render(request, "movie_detail.html", {"error": "Film non trouvé"})

    movie = filtered.iloc[0].copy()

    # 🎭 Genres
    movie['genres'] = ", ".join([
        genre.title() for genre in genre_columns if movie[genre] == 1
    ])

    # 🔥 CLEAN TITLE (important for TMDb)
    clean_title = movie["TITLE"].split("(")[0].strip()

    # =========================
    # 🎬 TMDb FIRST (poster)
    # =========================
    poster = get_movie_poster(clean_title)

    details = {
        "Poster": poster
    }

    # =========================
    # 🔄 FALLBACK OMDb (optional)
    # =========================
    if not poster:
        omdb_data = get_movie_details(clean_title)
        details.update(omdb_data)

    # =========================
    # 🧱 FINAL fallback
    # =========================
    if not details.get("Poster"):
        details["Poster"] = f"https://via.placeholder.com/250x375/333333/FFFFFF?text={clean_title}"

    # =========================
    # 👤 USER INFO
    # =========================
    user_id = request.session.get('user_id')
    user_rating = None
    in_watchlist_status = False

    if user_id:
        user_rating = get_user_rating(user_id, int(movie_id))
        in_watchlist_status = is_in_watchlist(user_id, int(movie_id))

        # 🎯 SIMILAR MOVIES
    similar_movies = recommend_similar_movies(int(movie_id), top_n=5)

    for m in similar_movies:
        m["Poster"] = get_movie_poster(m["TITLE"])

    return render(request, "movie_detail.html", {
        "movie": movie.to_dict(),
        "details": details,
        "user_rating": user_rating,
        "in_watchlist": in_watchlist_status,
        "user_id": user_id,
        "similar_movies": similar_movies
    })

    


def login(request):
    all_users = get_all_users().to_dict('records')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        if validate_user_login(user_id, password):
            request.session['user_id'] = int(user_id)
            messages.success(request, f"Connecté en tant qu'utilisateur {user_id}")
            return redirect('home')
        messages.error(request, "Identifiant ou mot de passe incorrect")

    return render(request, "login.html", {"users": all_users})


def logout(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    messages.success(request, "Déconnecté avec succès")
    return redirect('home')


# def rate_movie(request, movie_id):
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "Veuillez vous connecter pour noter un film")
#         return redirect('login')

#     if request.method == 'POST':
#         rating = request.POST.get('rating')
#         if rating:
#             add_rating(user_id, int(movie_id), int(rating))
#             messages.success(request, f"Film noté {rating} étoiles!")

#     return redirect('movie_detail', movie_id=movie_id)
def rate_movie(request, movie_id):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Veuillez vous connecter pour noter un film")
        return redirect('login')

    if request.method == 'POST':
        rating = request.POST.get('rating')

        # 🔥 DEBUG (optional)
        print("Rating received:", rating)

        if rating and rating.isdigit():
            rating = int(rating)

            if 1 <= rating <= 5:
                add_rating(user_id, int(movie_id), rating)
                messages.success(request, f"Film noté {rating} ⭐")
            else:
                messages.error(request, "Note invalide")
        else:
            messages.error(request, "Veuillez choisir une note")

    return redirect('movie_detail', movie_id=movie_id)
def get_user_rating(user_id, movie_id):
    movies, ratings, users, watchlist = load_data()

    user_rating = ratings[
        (ratings["USER_ID"] == user_id) &
        (ratings["MOVIE_ID"] == movie_id)
    ]

    if not user_rating.empty:
        return int(user_rating.iloc[-1]["RATINGS"])

    return None


def watchlist(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Veuillez vous connecter pour voir votre liste")
        return redirect('login')

    # 🔥 Get raw watchlist (only IDs)
    watchlist_raw = get_watchlist(user_id)

    watchlist_movies = []

    for item in watchlist_raw:
        movie = movies[movies["MOVIE_ID"] == item["MOVIE_ID"]]

        if not movie.empty:
            movie_data = movie.to_dict('records')[0]

            # ✅ Add poster
            movie_data["Poster"] = get_movie_poster(movie_data["TITLE"])

            watchlist_movies.append(movie_data)

    return render(request, "watchlist.html", {
        "watchlist": watchlist_movies,
        "user_id": user_id
    })
    


def add_to_watchlist_view(request, movie_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Veuillez vous connecter pour ajouter à la liste")
        return redirect('login')

    add_to_watchlist(user_id, int(movie_id))
    messages.success(request, "Film ajouté à votre liste à voir!")
    return redirect('movie_detail', movie_id=movie_id)


def remove_from_watchlist_view(request, movie_id):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Veuillez vous connecter")
        return redirect('login')

    remove_from_watchlist(user_id, int(movie_id))
    messages.success(request, "Film retiré de votre liste à voir!")
    return redirect('watchlist')


def profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Veuillez vous connecter pour voir votre profil")
        return redirect('login')

    user_ratings = get_user_ratings(user_id)
    rated_movies = []

    for _, row in user_ratings.iterrows():
        movie = movies[movies["MOVIE_ID"] == row['MOVIE_ID']]
        if not movie.empty:
            movie_data = movie.to_dict('records')[0]
            movie_data['rating'] = row['RATINGS']

            # ✅ ADD POSTER HERE
            movie_data["Poster"] = get_movie_poster(movie_data["TITLE"])

            rated_movies.append(movie_data)

    # ✅ WATCHLIST
    watchlist_movies = get_watchlist(user_id)
    for movie in watchlist_movies:
        movie["Poster"] = get_movie_poster(movie["TITLE"])

    # ✅ RECOMMENDATIONS
    recommendations_list = recommend_movies(user_id, top_n=10)
    rec_movies = []

    for title in recommendations_list:
        movie = movies[movies["TITLE"] == title]
        if not movie.empty:
            movie_data = movie.to_dict('records')[0]

            # ✅ ADD POSTER HERE
            movie_data["Poster"] = get_movie_poster(movie_data["TITLE"])

            rec_movies.append(movie_data)

    return render(request, "profile.html", {
        "user_id": user_id,
        "rated_movies": rated_movies,
        "watchlist": watchlist_movies,
        "recommendations": rec_movies
    })


def trending(request):
    # ✅ Get logged user
    user_id = request.session.get('user_id')

    # ✅ Connect to Snowflake
    conn = get_connection()

    # Load data
    movies, ratings, users, watchlist = load_data()

    conn.close()

    # =========================
    # 🎬 TOP 10 MOVIES (GLOBAL)
    # =========================
    top = ratings.groupby("MOVIE_ID")["RATINGS"].mean().sort_values(ascending=False).head(10)

    top_movies = movies[movies["MOVIE_ID"].isin(top.index)]

    rating_data = {
        "labels": top_movies["TITLE"].tolist(),
        "values": [round(v, 2) for v in top.values.tolist()]
    }

    # =========================
    # 🎭 GENRE DISTRIBUTION (GLOBAL)
    # =========================
    genre_columns = [
        'ACTION','ADVENTURE','ANIMATION','CHILDREN','COMEDY','CRIME',
        'DOCUMENTARY','DRAMA','FANTASY','FILM_NOIR','HORROR','MUSICAL',
        'MYSTERY','ROMANCE','SCI_FI','THRILLER','WAR','WESTERN'
    ]

    genre_counts = movies[genre_columns].sum().sort_values(ascending=False)

    genre_data = {
        "labels": genre_counts.index.tolist(),
        "values": genre_counts.values.tolist()
    }

    # =========================
    # 📊 USER STATS (PERSONALIZED)
    # =========================
    if user_id:
        user_ratings = ratings[ratings["USER_ID"] == int(user_id)]

        total_ratings = len(user_ratings)

        avg_rating = round(user_ratings["RATINGS"].mean(), 2) if total_ratings > 0 else 0

        # Favorite genre based on user's rated movies
        user_movies = movies[movies["MOVIE_ID"].isin(user_ratings["MOVIE_ID"])]

        if not user_movies.empty:
            genre_counts_user = user_movies[genre_columns].sum()
            top_genre = genre_counts_user.idxmax()
        else:
            top_genre = "N/A"
    else:
        total_ratings = 0
        avg_rating = 0
        top_genre = "N/A"

    # =========================
    # 🚀 SEND DATA TO TEMPLATE
    # =========================
    return render(request, "trending.html", {
        "rating_data": rating_data,
        "genre_data": genre_data,
        "total_ratings": total_ratings,
        "avg_rating": avg_rating,
        "top_genre": top_genre,
        "user_id": user_id   # ✅ VERY IMPORTANT for navbar
    })