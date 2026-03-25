# services/simulated_db.py
import pandas as pd
import snowflake.connector

# -------------------------
# Snowflake connection
# -------------------------
def get_connection():
    return snowflake.connector.connect(
        user='SAFAE',
        password='Safaebryar_123',
        account='KV90827.switzerland-north.azure',
        warehouse='COMPUTE_WH',
        database='MOVIE_RECOMMENDATION',
        schema='PUBLIC'
    )

# -------------------------
# Load tables from Snowflake
# -------------------------
def load_data():
    conn = get_connection()
    try:
        movies = pd.read_sql('SELECT * FROM MOVIES', conn)
        ratings = pd.read_sql('SELECT * FROM RATINGS', conn)
        users = pd.read_sql('SELECT * FROM USERS', conn)
        try:
            watchlist = pd.read_sql('SELECT * FROM WATCHLIST', conn)
        except Exception:
            watchlist = pd.DataFrame(columns=['USER_ID', 'MOVIE_ID'])
    finally:
        conn.close()
    return movies, ratings, users, watchlist

movies, ratings, users, watchlist = load_data()


# -------------------------
# USERS
# -------------------------
def get_all_users():
    return users.copy()

# def validate_user_login(user_id, password):
#     df = users[(users['USER_ID'] == int(user_id)) & (users['PASSWORD'] == password)]
#     return not df.empty


def validate_user_login(user_id_input, password):
    conn = get_connection()
    """
    Validate login using USER_ID and password.
    Returns integer USER_ID if valid, else None.
    """
    if not user_id_input or not password:
        return None  # missing input

    try:
        user_id_int = int(user_id_input)
    except ValueError:
        return None  # input was not a number

    query = f"SELECT * FROM USERS WHERE USER_ID = {user_id_int} AND PASSWORD = '{password}'"
    df = pd.read_sql(query, conn)

    if df.empty:
        return None  # no matching user

    # return the valid user_id
    return int(df.iloc[0]['USER_ID'])

# -------------------------
# RATINGS
# -------------------------
def get_user_ratings(user_id):
    return ratings[ratings['USER_ID'] == int(user_id)].copy()

def get_user_rating(user_id, movie_id):
    df = ratings[(ratings['USER_ID'] == int(user_id)) & (ratings['MOVIE_ID'] == int(movie_id))]
    if df.empty:
        return None
    return df.iloc[0]['RATINGS']

def add_rating(user_id, movie_id, rating):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            INSERT INTO RATINGS (USER_ID, MOVIE_ID, RATINGS)
            VALUES ({int(user_id)}, {int(movie_id)}, {int(rating)})
        """)
        conn.commit()
        # Update local DataFrame
        global ratings
        new_row = pd.DataFrame([{
            'USER_ID': int(user_id),
            'MOVIE_ID': int(movie_id),
            'RATINGS': int(rating)
        }])
        ratings = pd.concat([ratings, new_row], ignore_index=True)
    finally:
        cursor.close()
        conn.close()


# -------------------------
# WATCHLIST
# -------------------------
def get_watchlist(user_id):
    """Return all movies in the user's watchlist"""
    global watchlist
    wl = watchlist[watchlist['USER_ID'] == int(user_id)]
    result = []
    for _, row in wl.iterrows():
        movie = movies[movies['MOVIE_ID'] == row['MOVIE_ID']]
        if not movie.empty:
            result.append(movie.to_dict('records')[0])
    return result

def add_to_watchlist(user_id, movie_id):
    global watchlist
    if not is_in_watchlist(user_id, movie_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"""
                INSERT INTO WATCHLIST (USER_ID, MOVIE_ID)
                VALUES ({int(user_id)}, {int(movie_id)})
            """)
            conn.commit()
            # Update local DataFrame
            new_row = pd.DataFrame([{'USER_ID': int(user_id), 'MOVIE_ID': int(movie_id)}])
            watchlist = pd.concat([watchlist, new_row], ignore_index=True)
        finally:
            cursor.close()
            conn.close()

def remove_from_watchlist(user_id, movie_id):
    global watchlist
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            DELETE FROM WATCHLIST
            WHERE USER_ID = {int(user_id)} AND MOVIE_ID = {int(movie_id)}
        """)
        conn.commit()
        # Update local DataFrame
        watchlist = watchlist[~((watchlist['USER_ID'] == int(user_id)) & (watchlist['MOVIE_ID'] == int(movie_id)))]
    finally:
        cursor.close()
        conn.close()

def is_in_watchlist(user_id, movie_id):
    df = watchlist[(watchlist['USER_ID'] == int(user_id)) & (watchlist['MOVIE_ID'] == int(movie_id))]
    return not df.empty


