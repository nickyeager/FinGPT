
import pandas as pd
from datetime import datetime, timedelta, time
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
    snapshot_client = get_historic_client()
    positions = client.list_positions()
    current_timestamp = datetime.now()
    timestamp_format = '%Y-%m-%dT%H:%M:%S%z'
    if len(positions) > 0:
        positions = pd.DataFrame([position._raw for position in positions])
        positions.set_index('symbol', inplace=True)
    orders = client.list_orders()
    for news_item in news_items:
        article_timestamp = datetime.strptime(news_items[0].timestamp, timestamp_format)
        for article in news_item.ticker_sentiments:
            ticker = None
            try:
                ticker = article.ticker
            except:
                print("Ticker isn't defined")
            has_order = ticker != 'undefined' and len(orders) and [x for x in orders if x.symbol == ticker]
            has_position = ticker != 'undefined' and len(positions) and article.ticker in positions.index
            if has_order == False and has_position == False:
                snapshot = get_historic_data(client=snapshot_client, ticker=ticker)
                # get the current price, ideally right before the trade. This should happen within 5 minutes of the opening bell.
                last_trade_time = snapshot[ticker].latest_trade.timestamp
                side = article.side
                if last_trade_time.date() == article_timestamp.date() and current_timestamp.date() == article_timestamp.date():
                    try:
                        current_price = snapshot[ticker].latest_trade.price
                        trailing_price = 3  # Trailing stop percentage
                        trailing_loss_price = -3
                        trailing_stop_price = current_price * (1 - trailing_loss_price / 100)
                        trailing_take_profit = current_price * (1 - trailing_price / 100)
                        order = client.submit_order(symbol=ticker, qty=1, side=side, type="limit", limit_price=current_price, stop_loss={"stop_price": trailing_stop_price, "limit_price": trailing_take_profit}, time_in_force="gtc")
                        print(order)
                    except Exception as inst:
                        print(inst)


def get_cnbc_premarket():
    # news_item = PremarketArticle.PremarketArticle("Test Headline premarket", "https://www.cnbc.com/2023/08/11/stocks-moving-most-premarket-six-flags-ionq-archer-aviation-more.html")

    url = 'https://cnbc.com/market-insider/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    headlines = []
    news_items = []
    api_key = ALPACA_KEY
    secret = ALPACA_SECRET
    paper_url = ALPACA_URL

    url = URL(paper_url)

    a_client = REST(key_id=api_key, secret_key=secret, base_url=url)

    clock = a_client.get_clock()

    # Get the opening timestamp
    market_open_time = clock.next_open.replace(tzinfo=None)  # Convert to naive datetime

    print("Opening Timestamp:", market_open_time)

    # market_open_time = time(hour=9, minute=30)

    # Get the current Eastern Time
    current_time = datetime.now() - timedelta(
        hours=4)  # Alpaca timestamps are in Eastern Time (UTC-4 in daylight saving time)

    # Calculate the time difference between current time and market open time
    time_difference = current_time - market_open_time

    # Check if the time difference is within 30 minutes
    within_30_minutes = timedelta(minutes=0) <= time_difference <= timedelta(minutes=30)

    if within_30_minutes == False:
        print('Market not ready')
        return

    # only care about premarket headlines for now
    for headline in soup.find_all('a',
                                  class_='Card-title'):  # Adjust the class according to the website's HTML structure
        headline_text = headline.text.strip()
        is_premarket_headline = 'premarket' in headline_text.lower() or 'before the bell' in headline_text.lower()
        if is_premarket_headline:
            news_item = PremarketArticle.PremarketArticle(headline_text, headline['href'])
            news_items.append(news_item)
            headlines.append(headline_text)

    # Get the last news item
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

    place_trades(client=a_client, news_items=news_items)

    #check trades

if __name__ == '__main__':
    get_cnbc_premarket()
