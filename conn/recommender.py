import snowflake.connector
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from conn.test_snowflake import load_data


def create_user_movie_matrix(ratings):
    if ratings.empty:
        return pd.DataFrame()
    return ratings.pivot_table(
        index="USER_ID",
        columns="MOVIE_ID",
        values="RATINGS"
    ).fillna(0)


def compute_user_similarity(user_movie_matrix):
    if user_movie_matrix.empty:
        return pd.DataFrame()
    
    return pd.DataFrame(
        cosine_similarity(user_movie_matrix),
        index=user_movie_matrix.index,
        columns=user_movie_matrix.index
    )

def recommend_movies(user_id, top_n=5):
    movies, ratings, users, watchlist = load_data()

    if ratings.empty or movies.empty:
        print("No data found")
        return []

    user_movie_matrix = create_user_movie_matrix(ratings)

    if user_id not in user_movie_matrix.index:
        print("User not found")
        return []

    user_similarity = compute_user_similarity(user_movie_matrix)

    similar_users = user_similarity[user_id].sort_values(ascending=False).index[1:]

    user_movies = set(
        ratings[ratings["USER_ID"] == user_id]["MOVIE_ID"].values
    )

    recommended_movies = {}

    for sim_user in similar_users:
        sim_user_ratings = ratings[ratings["USER_ID"] == sim_user]

        for _, row in sim_user_ratings.iterrows():
            if row["MOVIE_ID"] not in user_movies and row["RATINGS"] >= 3:
                recommended_movies[row["MOVIE_ID"]] = \
                    recommended_movies.get(row["MOVIE_ID"], 0) + row["RATINGS"]

    recommended_movies = sorted(
        recommended_movies.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_movies = []

    for movie_id, score in recommended_movies[:top_n]:
        movie_row = movies[movies["MOVIE_ID"] == movie_id]

        if not movie_row.empty:
            title = movie_row["TITLE"].values[0]
            top_movies.append(title)

    return top_movies

movies, ratings, users, watchlist = load_data()
first_user = ratings["USER_ID"].iloc[0]
print(recommend_movies(user_id=first_user, top_n=5))


def recommend_similar_movies(movie_id, top_n=5):
    movies, ratings, users, watchlist = load_data()

    if movies.empty:
        return []

    genre_columns = [
        'ACTION','ADVENTURE','ANIMATION','CHILDREN','COMEDY','CRIME',
        'DOCUMENTARY','DRAMA','FANTASY','FILM_NOIR','HORROR','MUSICAL',
        'MYSTERY','ROMANCE','SCI_FI','THRILLER','WAR','WESTERN'
    ]

    # 🔹 Build movie-feature matrix (genres)
    movie_features = movies.set_index("MOVIE_ID")[genre_columns]

    if movie_id not in movie_features.index:
        return []

    # 🔹 Compute similarity
    similarity = cosine_similarity(movie_features)

    similarity_df = pd.DataFrame(
        similarity,
        index=movie_features.index,
        columns=movie_features.index
    )

    # 🔹 Get similar movies
    similar_scores = similarity_df[movie_id].sort_values(ascending=False)

    # Remove itself
    similar_scores = similar_scores.drop(movie_id)

    top_movies = []

    for sim_movie_id in similar_scores.head(top_n).index:
        movie_row = movies[movies["MOVIE_ID"] == sim_movie_id]
        if not movie_row.empty:
            top_movies.append(movie_row.iloc[0].to_dict())

    return top_movies