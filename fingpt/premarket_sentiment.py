
import pandas as pd

import openai

import requests
from bs4 import BeautifulSoup
from FinGPT_sentiment.Models import PremarketArticle, TickerSentiment

from alpaca_trade_api.rest import REST, TimeFrame, URL


from alpaca.data import StockHistoricalDataClient, StockSnapshotRequest
import os
from dotenv import load_dotenv

load_dotenv()

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
ALPACA_KEY = os.getenv('ALPACA_KEY')
ALPACA_SECRET = os.getenv('ALPACA_SECRET')
ALPACA_URL = os.getenv('ALPACA_URL')

# Function to search for a NewsItem based on the headline
def find_news_item_by_headline(news_items, target_headline):
    for news_item in news_items:
        if news_item.headline == target_headline:
            return news_item
    return None

def get_historic_client():
    return StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)

def get_historic_data(ticker: str, client: StockHistoricalDataClient):
    snapshot_request = StockSnapshotRequest(symbol_or_symbols=ticker)
    snapshot = client.get_stock_snapshot(snapshot_request)
    return snapshot

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

def convert_message_to_side(message: str):
    if ("mean-reversion-short" in message):
        return 'sell'

    if ("mean-reversion-long" in message):
        return 'buy'

    if ("trend-following-long" in message):
        return 'buy'

    if ("trend-following-short" in message):
        return 'sell'
    if ("hold" in message):
        return 'none'

def place_trades(client: REST, news_items: PremarketArticle):


    # query your current account. See if a position is already in place for that particular ticker. See if we've closed out that position today.
    positions = client.list_positions()
    if len(positions) > 0:
        positions = pd.DataFrame([position._raw for position in positions])
        positions.set_index('symbol', inplace=True)
    orders = client.list_orders()
    for news_item in news_items:
        for article in news_item.ticker_sentiments:
            has_order = len(orders) and [x for x in orders if x.symbol == article.ticker]
            has_position = len(positions) and article.ticker in positions.index
            if has_order == False and has_position == False:
                snapshot = get_historic_data(client=client, ticker=article.ticker)

                side = article.side
                try:
                    client.submit_order(symbol=article.ticker, qty=1, side=side)
                except Exception as inst:
                    print(inst)


def get_cnbc_premarket():
    url = 'https://cnbc.com/market-insider/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    headlines = []
    links = []
    nodes = []

    news_items = []
    for headline in soup.find_all('a',
                                  class_='Card-title'):  # Adjust the class according to the website's HTML structure
        news_item = PremarketArticle.PremarketArticle(headline.text.strip(), headline['href'])
        news_items.append(news_item)
        headlines.append(headline.text.strip())

    news_items = news_items[:3]
    # Step 2: Filter headlines containing the word "premarket"
    premarket_headlines = [headline for headline in headlines if 'premarket' in headline.lower()]
    # Step 3: Visit each link, fetch content, and extract articles and tickers
    for headline in premarket_headlines:

        found_news_item = find_news_item_by_headline(news_items, headline)
        if (found_news_item == None):
            break
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
            article_prompt_string = """Your a switch statement, only returning the following string based on the text passed in: 'mean-reversion-short', 'mean-reversion-long', 'trend-following-short', 'trend-following-long'. also, output a rating of 0-100 based on the severity of these ratings 
            If a stock has risen in premarket and according to the article summary rose because of an analysts recommendation or because of the news, return the text 'mean-reversion-short'.
            If a stock has fallen in premarket and according to the article fell because of a financial analysts change in recommendation or because of a news item ONLY return the text 'mean-reversion long'.
             If a stock has fallen in premarket and according to the article summary because of earnings ONLY return the text 'trend-following-long'
             If a stock has risen in premarket and according to the article summary because of earnings ONLY return the text'trend-following-short'
             If a stock price has changed because of an acquisition ONLY return 'hold'
            """
            mean_reversion_result = get_result_from_openai_gpt4([{"content": text + article_prompt_string, "role": "user"}])
            #found_news_item.meanSentiment = meanReversionResult
            choice = mean_reversion_result.choices[0].get('message').get('content')
            side = convert_message_to_side(choice)
            ticker_sentiment.side = side
            ticker_sentiment.meanSentiment = mean_reversion_result
            ticker_sentiment.parent = found_news_item
            found_news_item.ticker_sentiments.append(ticker_sentiment)

    # snapshot_client = get_historic_client()
    # for news_item in news_items:
    #     for article in news_item.ticker_sentiments:
    #         snapshot = get_historic_data(article.ticker, snapshot_client)
    #         print(snapshot)
    # print(news_items)
    api_key = ALPACA_KEY
    secret = ALPACA_SECRET
    paper_url = ALPACA_URL

    url = URL(paper_url)

    a_client = REST(key_id=api_key, secret_key=secret, base_url=url)
    place_trades(client=a_client, news_items=news_items)

if __name__ == '__main__':
    get_cnbc_premarket()
