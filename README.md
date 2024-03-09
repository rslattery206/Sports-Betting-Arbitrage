* You will need to obtain an API key from Odds API (https://the-odds-api.com/) and put it as a line in "keys.txt". \n
* Running main.py will start scanning for opportunities, and running interface.py will launch the interface. 
* Parameters for search can be changed in main()
* Arbitrage opportunities are recorded as ArbitrageOpportunity objects in .pk1 files. Analysis.py has tools for analysis:
  1. generate_csv(identifier) will use the current .pk1 files to create a csv.
  2. group_csv() will get arbitrage opportunities in a usable format
