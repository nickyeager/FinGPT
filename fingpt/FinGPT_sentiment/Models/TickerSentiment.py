class TickerSentiment:
    def __init__(self, ticker, link):
        self.link = link
        self.ticker = ticker
        self.text = None

        self.meanSentiment = None
        self.parent = None