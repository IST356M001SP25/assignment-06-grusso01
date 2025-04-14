import streamlit as st
import pandas as pd
import requests
import json 
if __name__ == "__main__":
    import sys
    sys.path.append('code')
    from apicalls import get_google_place_details, get_azure_sentiment, get_azure_named_entity_recognition
else:
    from code.apicalls import get_google_place_details, get_azure_sentiment, get_azure_named_entity_recognition

PLACE_IDS_SOURCE_FILE = "cache/place_ids.csv"
CACHE_REVIEWS_FILE = "cache/reviews.csv"
CACHE_SENTIMENT_FILE = "cache/reviews_sentiment_by_sentence.csv"
CACHE_ENTITIES_FILE = "cache/reviews_sentiment_by_sentence_with_entities.csv"


def reviews_step(place_ids: str|pd.DataFrame) -> pd.DataFrame:
    '''
      1. place_ids --> reviews_step --> reviews: place_id, name (of place), author_name, rating, text 
    '''
    if isinstance(place_ids, str):
        place_ids_df = pd.read_csv(place_ids)
    else:
        place_ids_df = place_ids 
    
    
    places = []
    for index, row in place_ids_df.iterrows():
        place = get_google_place_details(row['Google Place ID'])
        places.append(place['result'])
   
    review_df = pd.json_normalize(places, record_path="reviews", meta=["place_id", 'name'])
    review_df = review_df[['place_id', 'name',  'author_name', 'rating', 'text']]

    review_df.to_csv(CACHE_REVIEWS_FILE, index=False, header=True)
    return review_df



def sentiment_step(reviews: str|pd.DataFrame) -> pd.DataFrame:
    '''
      2. reviews --> sentiment_step --> review_sentiment_by_sentence
    '''
    if isinstance(reviews, str):
        review_df = pd.read_csv(reviews)
    else:
        review_df = reviews
    

    sentiments = []
    for index, row in review_df.iterrows():
        sentiment = get_azure_sentiment(row['text'])
        sentiment_response = sentiment['results']['documents'][0]
        sentiment_response['place_id'] = row['place_id']
        sentiment_response['name'] = row['name']
        sentiment_response['author_name'] = row['author_name']
        sentiment_response['rating'] = row['rating']
        sentiments.append(sentiment_response)

    sentiment_df = pd.json_normalize(sentiments, record_path="sentences", meta=["place_id", 'name', 'author_name', 'rating'])
    
    sentiment_df.rename(columns={
        'text': 'sentence_text',
        'sentiment': 'sentence_sentiment'
    }, inplace=True)

    sentiment_df = sentiment_df[['place_id', 'name', 'author_name', 'rating', 'sentence_text', 'sentence_sentiment', 'confidenceScores.positive', 'confidenceScores.neutral', 'confidenceScores.negative']]

    sentiment_df.to_csv(CACHE_SENTIMENT_FILE, index=False, header=True)
    return sentiment_df
    

def entity_extraction_step(sentiment: str|pd.DataFrame) -> pd.DataFrame:
    '''
      3. review_sentiment_by_sentence --> entity_extraction_step --> review_sentiment_entities_by_sentence
    '''
    if isinstance(sentiment, str):
        sentiment_df = pd.read_csv(sentiment)
    else:
        sentiment_df = sentiment

    entities = []
    for index, row in sentiment_df.iterrows():
        entity = get_azure_named_entity_recognition(row['sentence_text'])
        entity_response = entity['results']['documents'][0]
        for col in sentiment_df.columns:
            entity_response[col] = row[col]
        entities.append(entity_response)

    entity_df = pd.json_normalize(entities, record_path="entities", meta=["place_id", 'name', 'author_name', 'rating', 'sentence_text', 'sentence_sentiment', 'confidenceScores.positive', 'confidenceScores.neutral', 'confidenceScores.negative'])
    entity_df.rename(columns={
        'text': 'entity_text',
        'category': 'entity_category',
        'subCategory': 'entity_subCategory',
        'confidenceScore': 'confidenceScores.entity'
    }, inplace=True)

    entity_df = entity_df[['place_id', 'name', 'author_name', 'rating', 'sentence_text', 'sentence_sentiment', 'confidenceScores.positive', 'confidenceScores.neutral', 'confidenceScores.negative', 'entity_text', 'entity_category', 'entity_subCategory', 'confidenceScores.entity']]

    entity_df.to_csv(CACHE_ENTITIES_FILE, index=False, header=True)
    return entity_df





if __name__ == '__main__':
    # helpful for debugging as you can view your dataframes and json outputs
    import streamlit as st 
    st.write("What do you want to debug?")