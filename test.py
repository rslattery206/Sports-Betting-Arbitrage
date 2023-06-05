import pickle
from datetime import datetime, timedelta
from arbitrage_classes import ArbitrageManager, ArbitrageOpportunity

if __name__ == '__main__':
    with open('arbitrage_manager.pk1', 'rb') as file:
        arbitrage_manager = pickle.load(file)
    print(arbitrage_manager.print_opportunities())
    print(arbitrage_manager.get_opportunities()[0].odds1)
