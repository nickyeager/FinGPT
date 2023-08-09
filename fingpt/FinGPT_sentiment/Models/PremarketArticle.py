class PremarketArticle:
    def __init__(self, headline, link):
        self.headline = headline
        self.link = link
        self.timestamp = None
        self.ticker_sentiments = []