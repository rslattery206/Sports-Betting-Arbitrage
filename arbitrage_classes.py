def decimal_to_american(decimal):
    if decimal == 1:
        return -10000
    if decimal >= 2.0:
        american_odds = (decimal - 1) * 100
        return int(american_odds)
    else:
        american_odds = -100 / (decimal - 1)
        return int(american_odds)


class ArbitrageManager:
    def __init__(self, existing=None):
        if existing:
            # existing object of the ArbitrageManager class
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

    def print_opportunities(self):
        if len(self.opportunities) == 0:
            return
        print("Number of Opportunities: " + str(len(self.opportunities)))
        for arbitrage_opportunity in self.opportunities:
            print("Sport: " + str(arbitrage_opportunity.sport) + " starting at: " + str(arbitrage_opportunity.gametime))
            print("Team1: " + str(arbitrage_opportunity.team1) + " on " +
                  str(arbitrage_opportunity.bookmaker1) + " with odds: " + str(arbitrage_opportunity.odds1) +
                  " aka " + str(decimal_to_american(arbitrage_opportunity.odds1)))
            print("Team2: " + str(arbitrage_opportunity.team2) + " on " +
                  str(arbitrage_opportunity.bookmaker2) + " with odds: " + str(arbitrage_opportunity.odds2) +
                  " aka " + str(decimal_to_american(arbitrage_opportunity.odds2)))
            if arbitrage_opportunity.draw_odds_bookie is not None:
                print('Draw on ' + str(arbitrage_opportunity.draw_odds_bookie) +
                      " with odds: " + str(arbitrage_opportunity.draw_odds))
            print("Total Implied Prob: " + str(arbitrage_opportunity.total_implied_prob))
            print("Betting Amounts: ")
            print("1: " + str(arbitrage_opportunity.bet1))
            print("2: " + str(arbitrage_opportunity.bet2))
            if arbitrage_opportunity.bet3:
                print("Draw: " + str(arbitrage_opportunity.bet3))
            print('\n')

    def get_n_opportunities(self):
        return len(self.opportunities)


class ArbitrageOpportunity:
    def __init__(self, recorded_time, gametime, sport, team1, team2, bookmaker1, bookmaker2,
                 odds1, odds2, last_update1, last_update2, draw_odds_bookie=None, draw_odds=None):
        self.recorded_time = recorded_time
        self.gametime = gametime
        self.sport = sport
        self.team1 = team1
        self.team2 = team2
        self.bookmaker1 = bookmaker1
        self.bookmaker2 = bookmaker2
        self.odds1 = odds1
        self.odds2 = odds2
        self.draw_odds = draw_odds
        self.draw_odds_bookie = draw_odds_bookie
        self.total_implied_prob = self.calculate_total_implied_prob()
        self.last_update1 = last_update1
        self.last_update2 = last_update2
        self.bet1, self.bet2 = self.find_whole_betting_amounts()
        self.bet3 = None  # No soccer

    def get_betting_amounts(self, bet_total=100, draw_odds=0):
        # doesn't work
        if draw_odds == 0:
            bet1 = (bet_total / self.odds1) / (1 / self.odds1 + self.odds2)
            bet2 = (bet_total / self.odds2) / (1 / self.odds1 + self.odds2)
            return [bet1, bet2, None]
        else:
            bet1 = (bet_total / self.odds1) / (1 / self.odds1 + self.odds2 + self.draw_odds)
            bet2 = (bet_total / self.odds2) / (1 / self.odds1 + self.odds2 + self.draw_odds)
            bet3 = (bet_total / self.draw_odds) / (1 / self.odds1 + self.odds2 + self.draw_odds)
            return [bet1, bet2, bet3]

    def find_whole_betting_amounts(self):
        # finds whole number betting amounts with varying profit margins
        # can produce negative profits... tends to be more likely with smaller profit margins
        # TODO: only optimized by rounding <.05 and >.95 -- Should round by a percentage or something
        odds1 = self.odds1
        odds2 = self.odds2
        bet1 = 1
        bet2 = bet1 * odds1 / odds2
        altbet2 = 1
        altbet1 = altbet2 * odds2 / odds1

        while True:
            if bet2 == int(bet2) or round(bet2, 1) == int(bet2):
                return [bet1, round(bet2, 1)]
            elif altbet1 == int(altbet1) or round(altbet1, 1) == int(altbet1):
                return [round(altbet1, 1), altbet2]
            else:
                bet1 += 1
                bet2 = bet1 * odds1 / odds2
                altbet2 += 1
                altbet1 = altbet2 * odds2 / odds1

    def calculate_total_implied_prob(self):
        if self.draw_odds is None or self.draw_odds == 0:
            return (1 / self.odds1) + (1 / self.odds2)
        else:
            return (1 / self.odds1) + (1 / self.odds2) + (1 / self.draw_odds)


class Combination:
    # Combination is used to define an opportunity without its recorded time or update times.
    # arbitrageopportunity is of ArbitrageOpportunity class
    def __init__(self, arbitrageopportunity):
        self.gametime = arbitrageopportunity.gametime
        self.sport = arbitrageopportunity.sport
        self.total_implied_prob = arbitrageopportunity.total_implied_prob
        self.team1 = arbitrageopportunity.team1
        self.team2 = arbitrageopportunity.team2
        self.bookmaker1 = arbitrageopportunity.bookmaker1
        self.bookmaker2 = arbitrageopportunity.bookmaker2
        self.odds1 = arbitrageopportunity.odds1
        self.odds2 = arbitrageopportunity.odds2
        self.draw_odds = arbitrageopportunity.draw_odds
        self.draw_odds_bookie = arbitrageopportunity.draw_odds_bookie
        self.bet1, self.bet2 = ArbitrageOpportunity.find_whole_betting_amounts(arbitrageopportunity)
        self.lifespan1 = 0
        self.lifespan2 = 0

    def add_lifespan(self, seconds1, seconds2):
        self.lifespan1 += seconds1
        self.lifespan2 += seconds2
        return self

    def get_expected_profits(self):
        return (self.bet1 * self.odds1 - self.bet1 - self.bet2), (self.bet2 * self.odds2 - self.bet1 - self.bet2)

    def __eq__(self, other):
        if not isinstance(other, Combination):
            return False

        return (
                self.gametime == other.gametime
                and self.sport == other.sport
                and self.total_implied_prob == other.total_implied_prob
                and self.team1 == other.team1
                and self.team2 == other.team2
                and self.bookmaker1 == other.bookmaker1
                and self.bookmaker2 == other.bookmaker2
                and self.odds1 == other.odds1
                and self.odds2 == other.odds2
                and self.draw_odds == other.draw_odds
                and self.draw_odds_bookie == other.draw_odds_bookie
        )

    def __hash__(self):
        return hash((
            self.gametime,
            self.sport,
            self.total_implied_prob,
            self.team1,
            self.team2,
            self.bookmaker1,
            self.bookmaker2,
            self.odds1,
            self.odds2,
            self.draw_odds,
            self.draw_odds_bookie
        ))
