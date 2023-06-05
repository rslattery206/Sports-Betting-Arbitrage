class ArbitrageManager:
    def __init__(self):
        self.opportunities = []  # list of ArbitrageOpportunity Objects

    def add_opportunity(self, opportunity):
        self.opportunities.append(opportunity)

    def remove_opportunity(self, opportunity):
        self.opportunities.remove(opportunity)

    def get_opportunities(self):
        return self.opportunities

    def print_opportunities(self):
        print("Number of Opportunities: " + str(len(self.opportunities)))
        for arbitrage_opportunity in self.opportunities:
            print("Sport: " + str(arbitrage_opportunity.sport) + " starting at: " + str(arbitrage_opportunity.gametime))
            print("Team1: " + str(arbitrage_opportunity.team1) + " on " + str(
                arbitrage_opportunity.bookmaker1) + " with odds: " + str(arbitrage_opportunity.odds1))
            print("Team2: " + str(arbitrage_opportunity.team2) + " on " + str(
                arbitrage_opportunity.bookmaker2) + " with odds: " + str(arbitrage_opportunity.odds2))
            print("Total Implied Prob: " + str(arbitrage_opportunity.total_implied_prob))
            print('\n')


class ArbitrageOpportunity:
    def __init__(self, gametime, sport, team1, team2, bookmaker1, bookmaker2, odds1, odds2, draw_odds=None):
        self.gametime = gametime
        self.sport = sport
        self.team1 = team1 # Team 1 name
        self.team2 = team2
        self.bookmaker1 = bookmaker1
        self.bookmaker2 = bookmaker2
        self.odds1 = odds1 # Price1
        self.odds2 = odds2
        self.draw_odds = draw_odds
        self.total_implied_prob = self.calculate_total_implied_prob()

    def calculate_total_implied_prob(self):
        if self.draw_odds is None:
            return (1 / self.odds1) + (1 / self.odds2)
        else:
            return (1 / self.odds1) + (1 / self.odds2) + (1 / self.draw_odds)
