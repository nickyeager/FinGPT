import os.path
import json

import http.client
import urllib.parse

import pandas as pd
import tushare as ts

import os
import openai

import requests
from bs4 import BeautifulSoup
from FinGPT_sentiment.Models import PremarketArticle, TickerSentiment

from alpaca_trade_api.rest import REST, TimeFrame

from alpaca.data import StockHistoricalDataClient, StockSnapshotRequest


def get_news_from_tushare(api_key: str, data_path: str = 'finance_news_from_tushare.csv') -> str:
    start_date = '2023-02-01'
    end_date = '2023-02-02'
    limit_line = 200
    if_news_or_reports = False

    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
    else:
        pro = ts.pro_api(api_key)

        if if_news_or_reports:
            df = pro.news(**{
                "start_date": start_date,
                "end_date": end_date,
                "src": "sina",
                "limit": limit_line,
                "offset": 0
            }, fields=[
                "datetime",
                "title"
                "content",
            ])
        else:
            df = pro.jinse(**{
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit_line,
                "offset": 0
            }, fields=[
                "datetime",
                "title",
                "content",
            ])

        df.to_csv(data_path)

    max_num_news = 4
    max_len_title = 32
    max_len_content = 0
    data_str = ""
    for i in df.index[:max_num_news]:
        row = df.iloc[i]
        title = row['title'][1:max_len_title]
        content = row['content'][:max_len_content]
        data_str += f"{title}, {content}\n"
    return data_str


def get_news_from_market_aux(api_key: str, data_path: str = 'finance_news_from_market_aux.txt'):
    limit_line = 4

    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)
    else:
        conn = http.client.HTTPSConnection('api.marketaux.com')

        params = urllib.parse.urlencode({
            'api_token': api_key,
            "found": 8,
            "returned": 3,
            "limit": limit_line,
            "page": 1,
            "source_id": "adweek.com-1",
            "domain": "adweek.com",
            "language": "en",
        })

        conn.request('GET', '/v1/news/all?{}'.format(params))

        data = conn.getresponse()
        data = data.read().decode('utf-8')
        data = json.loads(data)
        with open(data_path, 'w') as f:
            f.write(json.dumps(data, indent=2))

    assert isinstance(data, dict)

    '''concert dict to string (Title: ... Content: ...)'''
    max_num_news = 8
    max_len_title = 32 * 4
    max_len_content = 0 * 4

    data = data['data']

    data_str = ""
    for item in data[:max_num_news]:
        title = item['title'][:max_len_title]
        content = item['description'][:max_len_content]
        data_str += f"{title}, {content}\n"
    return data_str

class Article:
    def __init__(self, headline, link):
        self.headline = headline
        self.link = link
        self.timestamp = None

class TextItem:
    def __init__(self, headline, link):
        self.headline = headline
        self.link = link
        self.text = None
        self.ticker = None
        self.meanSentiment = None
        self.parent = None


# Function to search for a NewsItem based on the headline
def find_news_item_by_headline(news_items, target_headline):
    for news_item in news_items:
        if news_item.headline == target_headline:
            return news_item
    return None

def get_historic_client():
    return StockHistoricalDataClient("PKC4NOQ50FZYDSDTA30H", "I1OOp7YE6zlIw2auuGULyWG0C8KLoZhacxdEUT07")

def get_historic_data(ticker: str, client: StockHistoricalDataClient):
    snapshot_request = StockSnapshotRequest(symbol_or_symbols=ticker)
    snapshot = client.get_stock_snapshot(snapshot_request)
    return snapshot

def get_moving_average_by_day(ticker: str, client: REST, days: str):
    barset = client.get_barset(ticker, 'day', limit=days)

def get_result_from_openai_gpt4( prompt_str: str):
    max_tokens = 64
    openai.api_key = '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'
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

def get_cnbc_premarket():
    # Step 1: Fetch website content and extract headlines and links
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
        # links.append(headline['href'])
        # nodes.append(headline)



    # news_items = [PremarketArticle.PremarketArticle(headline, link) for headline, link in zip(headlines, links)]

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
        # premarket_article = article_soup
        all_articles = article_soup.find_all('span', class_='QuoteInBody-quoteNameContainer')
        for an_article in all_articles:
            text = an_article.parent.text.strip()
            ticker = an_article.find('a')['href'].split('/')
            ticker = ticker[2]
            ticker_sentiment = TickerSentiment.TickerSentiment(ticker, text)
            article_prompt_string = """Designate the above article on whether it should be designated as 'mean-reversion-short', 'mean-reversion-long', 'trend-following-short', 'trend-following-long'. 
            If a stock has risen in premarket and according to the article summary rose because of an analysts recommendation or because of the news, designate it as 'mean-reversion-short'.
            If a stock has fallen in premarket and according to the article fell because of a financial analysts change in recommendation or because of a news item, designate it as a 'mean-reversion long'.
             If a stock has fallen in premarket and according to the article summary because of earnings, designate it as 'trend-following-long'
             If a stock has risen in premarket and according to the article summary because of earnings, designate it as 'trend-following-short';;
            """
            meanReversionResult = get_result_from_openai_gpt4([{"content": text + article_prompt_string, "role": "user"}])
            #found_news_item.meanSentiment = meanReversionResult
            ticker_sentiment.meanSentiment = meanReversionResult
            ticker_sentiment.parent = found_news_item
            found_news_item.ticker_sentiments.append(ticker_sentiment)

    # conn = http.client.HTTPSConnection('cnbc.com/market-insider/')
    # conn.request('GET', '')
    # data = conn.getresponse()

    snapshot_client = get_historic_client()
    for news_item in news_items:
        for article in news_item.ticker_sentiments:
            snapshot = get_historic_data(article.ticker, snapshot_client)
            print(snapshot)
    print(news_items)


if __name__ == '__main__':
    get_cnbc_premarket()
    #run_news_in_chinese()
    # run_news_in_english()
