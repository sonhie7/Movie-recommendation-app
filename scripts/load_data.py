import pandas as pd


query = "SELECT user_id, movie_id, rating FROM ratings;"
ratings_df = pd.read_sql(query, conn)

ratings_df.head()
ratings_df.isnull().sum()  # Vérifier les valeurs manquantes