import vectorbt as vbt
import os
from dotenv import load_dotenv

load_dotenv()

from scrapers.Models import *
from scrapers.Prompts import *

from scrapers.cnbc_scraper import *

OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
ALPACA_KEY = os.getenv('ALPACA_KEY')
ALPACA_SECRET = os.getenv('ALPACA_SECRET')
ALPACA_URL = os.getenv('ALPACA_URL')

vbt.settings.data['alpaca']['key_id'] = ALPACA_KEY
vbt.settings.data['alpaca']['secret_key'] = ALPACA_SECRET

url = "https://cnbc.com/market-insider"



# start date

scrape_cnbc_premarket(url, 1)

#end date




# get the tickers, side and date

# create a class that just extracts all premarket urls
# alpacadata = vbt.AlpacaData.download_symbol(symbol='AAPL', start='4 days ago UTC', end='1 day ago UTC', timeframe='1h')
# alpacadata.get_data()