StockClassificationV1 = """Your a switch statement, only returning the following string based on the text passed in: 'mean-reversion-short', 'mean-reversion-long', 'trend-following-short', 'trend-following-long'. also, output a rating of 0-100 based on the severity of these ratings 
  If a stock has risen in premarket and according to the article summary rose because of an analysts recommendation or because of the news, return the text 'mean-reversion-short'.
  If a stock has fallen in premarket and according to the article fell because of a financial analysts change in recommendation or because of a news item ONLY return the text 'mean-reversion long'.
   If a stock has fallen in premarket and according to the article summary because of earnings ONLY return the text 'trend-following-long'
   If a stock has risen in premarket and according to the article summary because of earnings ONLY return the text'trend-following-short'
   If a stock price has changed because of an acquisition ONLY return 'hold'
  """

StockClassificationEarningsTrendingV1 = """Your a switch statement, only returning the following string based on the text passed in: 'mean-reversion-short', 'mean-reversion-long', 'trend-following-short', 'trend-following-long'. also, output a rating of 0-100 based on the severity of these ratings 
  If a stock has risen in premarket and according to the article summary rose because of an analysts recommendation or because of the news, return the text 'mean-reversion-short'.
  If a stock has fallen in premarket and according to the article fell because of a financial analysts change in recommendation or because of a news item ONLY return the text 'mean-reversion long'.
   If a stock has fallen in premarket and according to the article summary because of earnings ONLY return the text 'trend-following-short'
   If a stock has risen in premarket and according to the article summary because of earnings ONLY return the text'trend-following-long'
   If a stock price has changed because of an acquisition ONLY return 'hold'
  """

class Prompts:

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