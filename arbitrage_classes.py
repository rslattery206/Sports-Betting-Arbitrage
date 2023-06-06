class ArbitrageManager:
    def __init__(self, existing=None):
        if existing:
            self.opportunities = existing.get_opportunities()
        else:
            self.opportunities = []  # list of ArbitrageOpportunity Objects

    def add_opportunity(self, opportunity):
        self.opportunities.append(opportunity)

    def remove_opportunity(self, opportunity):
        self.opportunities.remove(opportunity)

    def get_opportunities(self):
        return self.opportunities

    def sort_opportunities(self, key='total_implied_prob'):
        self.opportunities.sort(key=lambda x: getattr(x, key))
        return self.opportunities

    def filter(self):
        x = "BetUS"
        y = []
        for opp in self.opportunities:
            if not (opp.bookmaker1 == x or opp.bookmaker2 == x):
                y.append(opp)
        self.opportunities = y
        return self.opportunities

    def decimal_to_american(self, decimal):
        if decimal == 1:
            return -10000
        if decimal >= 2.0:
            american_odds = (decimal - 1) * 100
            return int(american_odds)
        else:
            american_odds = -100 / (decimal - 1)
            return int(american_odds)

    def print_opportunities(self):
        print("Number of Opportunities: " + str(len(self.opportunities)))
        for arbitrage_opportunity in self.opportunities:
            print("Sport: " + str(arbitrage_opportunity.sport) + " starting at: " + str(arbitrage_opportunity.gametime))
            print("Team1: " + str(arbitrage_opportunity.team1) + " on " +
                  str(arbitrage_opportunity.bookmaker1) + " with odds: " + str(arbitrage_opportunity.odds1) +
                  " aka " + str(self.decimal_to_american(arbitrage_opportunity.odds1)))
            print("Team2: " + str(arbitrage_opportunity.team2) + " on " +
                  str(arbitrage_opportunity.bookmaker2) + " with odds: " + str(arbitrage_opportunity.odds2) +
                  " aka " + str(self.decimal_to_american(arbitrage_opportunity.odds2)))
            if arbitrage_opportunity.draw_odds:
                print('Draw on ' + str(arbitrage_opportunity.draw_odds_bookie) +
                      " with odds: " + str(arbitrage_opportunity.draw_odds))
            print("Total Implied Prob: " + str(arbitrage_opportunity.total_implied_prob))
            print("Team1 Last Updated: " + str(arbitrage_opportunity.last_update1))
            print("Team2 Last Updated: " + str(arbitrage_opportunity.last_update2))
            print('\n')


class ArbitrageOpportunity:
    def __init__(self, gametime, sport, team1, team2, bookmaker1, bookmaker2,
                 odds1, odds2, last_update1, last_update2, draw_odds_bookie=None, draw_odds=None):
        self.gametime = gametime
        self.sport = sport
        self.team1 = team1 # Team 1 name
        self.team2 = team2
        self.bookmaker1 = bookmaker1
        self.bookmaker2 = bookmaker2
        self.odds1 = odds1 # Price1
        self.odds2 = odds2
        self.draw_odds = draw_odds
        self.draw_odds_bookie = draw_odds_bookie  # Bookie name with the optimal drawing odds
        self.total_implied_prob = self.calculate_total_implied_prob()
        self.last_update1 = last_update1
        self.last_update2 = last_update2

    def get_betting_amounts(self, price1, price2, bet_total=100, draw=None):
        if not draw:
            self.bet1 = bet_total * ((1 / price1) - (1 / self.calculate_total_implied_prob())) / (
                        (1 / price1) + (1 / price2) - 2 / self.calculate_total_implied_prob())
            self.bet2 = bet_total * (1 - self.bet1)
        else:
            self.bet1 = bet_total * (
                        (1 / price1) - (1 / self.calculate_total_implied_prob()) / (1 / price1) + (1 / price2) + (
                            1 / draw) - (3 / self.calculate_total_implied_prob()))
            self.bet2 = bet_total * (
                        (1 / price2) - (1 / self.calculate_total_implied_prob()) / (1 / price1) + (1 / price2) + (
                            1 / draw) - (3 / self.calculate_total_implied_prob()))
            self.bet3 = bet_total * (1 - self.bet1 - self.bet2)

    def calculate_total_implied_prob(self):
        if self.draw_odds is None or self.draw_odds == 0:
            return (1 / self.odds1) + (1 / self.odds2)
        else:
            return (1 / self.odds1) + (1 / self.odds2) + (1 / self.draw_odds)
