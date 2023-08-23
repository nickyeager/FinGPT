import requests
from bs4 import BeautifulSoup
import urllib
import sys
sys.path.append("../Models")

from Models import PremarketArticle, TickerSentiment

# Tested: python src/scrapers/cnbc/scrape_cnbc.py https://www.cnbc.com/2020/01/02/fda-issues-ban-on-some-flavored-vaping-products.html "FDA issues ban on some fruit and mint flavored vaping products"
# https://www.cnbc.com/2019/12/06/amazon-blames-holiday-delivery-delays-on-winter-storms-and-high-demand.html?__source=twitter%7Cmain "Amazon blames holiday delivery delays on winter storms and high demand"

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