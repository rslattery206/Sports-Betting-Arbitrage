import pickle
from datetime import datetime, timedelta
from arbitrage_classes import ArbitrageManager, ArbitrageOpportunity
from main import total_implied_prob

if __name__ == '__main__':
    with open('arbitrage_manager.pk1', 'rb') as file:
        arbitrage_manager = pickle.load(file)

    arbitrage_manager = ArbitrageManager(arbitrage_manager)
    print(arbitrage_manager.get_opportunities()[0].odds1)
    arbitrage_manager.filter()
    arbitrage_manager.sort_opportunities('gametime')
    print(arbitrage_manager.print_opportunities())
    print(total_implied_prob(5.3, 2.25, 2.16))