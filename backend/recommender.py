import pandas as pd
import sqlite3
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack

# Define file paths for saving the trained model
SIMILARITY_MATRIX_PATH = 'similarity_matrix.pkl'
GAME_INDICES_PATH = 'game_indices.pkl'
GAME_LIST_PATH = 'game_list.pkl'


def load_data(db_path):
    """ Loads games from the SQLite database into a pandas DataFrame. """
    print("Loading data from database...")
    con = sqlite3.connect(db_path)
    # Load only the columns needed for the recommender
    df = pd.read_sql_query("SELECT id, name, summary, genres_json, keywords_json FROM games", con)
    con.close()
    print(f"Loaded {len(df)} games.")
    return df


def preprocess_data(df):
    """ Cleans and preprocesses the DataFrame. """
    print("Preprocessing data...")
    # Fill any missing summaries with an empty string
    df['summary'] = df['summary'].fillna('')

    # Function to parse JSON strings and extract names/IDs
    def parse_json_to_list(json_str):
        try:
            # The data is stored as a string of a list of numbers
            # e.g., '[12, 31]'
            return ' '.join(map(str, json.loads(json_str)))
        except (json.JSONDecodeError, TypeError):
            return ''

    # Apply the parsing function to genres and keywords
    df['genres_str'] = df['genres_json'].apply(parse_json_to_list)
    df['keywords_str'] = df['keywords_json'].apply(parse_json_to_list)

    # Create a combined text 'soup' for vectorization
    df['soup'] = df['summary'] + ' ' + df['genres_str'] + ' ' + df['keywords_str']
    return df


def create_model(df):
    """ Creates the feature vectors and computes the similarity matrix. """
    print("Creating feature vectors...")

    # Vectorize the 'soup' (summary + genres + keywords) using TF-IDF
    # This captures the most important words and tags for each game
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['soup'])

    print("Calculating cosine similarity matrix...")
    # This is the core calculation. It can take some time and memory.
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    return cosine_sim


def save_model(similarity_matrix, df):
    """ Saves the similarity matrix and game indices to disk. """
    print("Saving model files...")

    # Create a mapping from game ID to dataframe index
    indices = pd.Series(df.index, index=df['id']).to_dict()

    # Save the similarity matrix
    with open(SIMILARITY_MATRIX_PATH, 'wb') as f:
        pickle.dump(similarity_matrix, f)

    # Save the game ID to index mapping
    with open(GAME_INDICES_PATH, 'wb') as f:
        pickle.dump(indices, f)

    # Also save a simplified list of games for easy lookup later
    game_list = df[['id', 'name']].to_dict(orient='records')
    with open(GAME_LIST_PATH, 'wb') as f:
        pickle.dump(game_list, f)

    print(f"Model saved! Matrix shape: {similarity_matrix.shape}")


def train_and_save_model(db_path):
    """ The main function to run the full training pipeline. """
    df = load_data(db_path)
    df_processed = preprocess_data(df)
    similarity_matrix = create_model(df_processed)
    save_model(similarity_matrix, df_processed)