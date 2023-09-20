import requests
from bs4 import BeautifulSoup
import urllib
import sys
import openai
import os
from dotenv import load_dotenv
load_dotenv()

from Models import PremarketArticle, TickerSentiment
from Prompts import PremarketStockClassification
# from Prompts.PremarketStockClassification import Prompts
# import Prompts

import API
OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')

def requests_get(url):
    try:
        return requests.get(url)
    except Exception as e:
        print(f"Exception occurred while trying to get url: {url}, error: {str(e)}")
        return None

def similarity_score(a, b):
    words_a = a.split()
    words_b = b.split()
    matching_words = 0

    for word_a in words_a:
        for word_b in words_b:
            if word_a in word_b or word_b in word_a:
                matching_words += 1
                break

    similarity = matching_words / min(len(words_a), len(words_b))
    return similarity

def url_encode_string(input_string):
    encoded_string = urllib.parse.quote(input_string)
    return encoded_string

def check_headline_content(headline, search_terms):
    for term in search_terms:
        if term in headline.lower():
            return True
    return False


def get_result_from_openai_gpt4( prompt_str: str):
    max_tokens = 64
    openai.api_key = OPEN_AI_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=prompt_str,
        temperature=0,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response

def scrape_cnbc_premarket(url, page):
    try:
        news_items = []
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        print("Response content, ", response.content)
        for headline in soup.find_all('a',
                                      class_='Card-title'):  # Adjust the class according to the website's HTML structure
            headline_text = headline.text.strip()
            is_premarket_headline = check_headline_content(headline_text.lower(), ['premarket', 'before the bell'])

            if is_premarket_headline:
                news_item = PremarketArticle.PremarketArticle(headline_text, headline['href'])
                news_items.append(news_item)

        news_items = news_items[:1]
        for found_news_item in news_items:
            article_response = requests.get(found_news_item.link)
            article_soup = BeautifulSoup(article_response.content, 'html.parser')
            time = article_soup.find('time').get('datetime')

            found_news_item.timestamp = time
            all_articles = article_soup.find_all('span', class_='QuoteInBody-quoteNameContainer')
            for an_article in all_articles:
                text = an_article.parent.text.strip()
                ticker = an_article.find('a')['href'].split('/')
                ticker = ticker[2]
                ticker_sentiment = TickerSentiment.TickerSentiment(ticker, text)
                article_prompt_string = PremarketStockClassification.StockClassificationV1
                mean_reversion_result = get_result_from_openai_gpt4([{"content": text + article_prompt_string, "role": "user"}])
                #found_news_item.meanSentiment = meanReversionResult
                choice = mean_reversion_result.choices[0].get('message').get('content')
                side = Prompts.Prompts.convert_message_to_side(choice)
                ticker_sentiment.side = side

                ticker_sentiment.mean_sentiment = mean_reversion_result
                ticker_sentiment.parent = found_news_item
                found_news_item.ticker_sentiments.append(ticker_sentiment)

        return news_items

    except Exception as e:
        print("Exception in scrape_cnbc_article_page:", e)
        return "N/A", url

if __name__ == '__main__':
    # Check that the right number of command line arguments are provided
    # if len(sys.argv) != 3:
    #     print("Usage: python script_name.py <article_link> <subject>")
    #     exit(1)

    # Extract the arguments
    url = "https://cnbc.com/market-insider"


    result = scrape_cnbc_premarket(url, 1)
    print("Scraped Result:", result)