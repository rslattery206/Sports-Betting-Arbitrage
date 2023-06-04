import requests
from datetime import datetime, timedelta
import pytz

# 279c7cb0a5d77305c981038882f61408
# 462642ce457fcd2071b969b5387e89a4

def get():
    sport = 'baseball_mlb'
    key = '462642ce457fcd2071b969b5387e89a4'
    mkt = 'h2h'
    region = 'us'
    params = {'apiKey': key, 'region': region, 'mkt': mkt}
    url = f'https://api.the-odds-api.com/v4/sports/' \
          f'{sport}/odds/' \
          f'?apiKey={key}' \
          f'&regions={region}' \
          f'&markets={mkt}'
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json(), sport
    else:
        print('call returned error')
        return resp.status_code


def implied_prob(price):
    if price < 0:
        odds = -price / (-price + 100)
    else:
        odds = 100 / (price + 100)
    return odds


def total_implied_prob(price1, price2, draw):
    if draw == 0:
        return (1/price1) + (1/price2)
    else:
        return (1/price1) + (1/price2) + (1/draw)


if __name__ == '__main__':
    sport = 'baseball_mlb'
    resp, sport = get()

    for game_index in range(0, len(resp)):
        odds_list = []

        # Only consider games that haven't begun.
        threshold = 30
        game_time_str = resp[game_index]['commence_time']
        parsed_date = datetime.strptime(game_time_str, "%Y-%m-%dT%H:%M:%SZ")
        current_date = datetime.utcnow()
        pacific_tz = pytz.timezone('America/Los_Angeles')
        game_time_utc = pytz.utc.localize(parsed_date)
        converted_date = game_time_utc.astimezone(pacific_tz)
        future_threshold = current_date + timedelta(minutes=threshold)
        is_future = parsed_date > future_threshold

        if is_future:
            x = (resp[game_index]['bookmakers'])
            # Extract bookie, odds, team names, and game time.
            for i in range(0, len(x)):
                title = x[i]['title']
                moneyline = x[i]['markets'][0]['outcomes']
                team1_name = moneyline[0]['name']
                team1_price = moneyline[0]['price']
                team2_name = moneyline[1]['name']
                team2_price = moneyline[1]['price']
                draw = 0
                if sport == 'soccer':
                    draw = moneyline[2]['price']

                odds_list.append([title, team1_price, team2_price, team1_name, team2_name, str(converted_date), draw])
            print(odds_list)
            for i in odds_list:
                for j in odds_list:
                    if i != j:
                        tip = (total_implied_prob(i[1], j[2], min(i[6], j[6])))
                        if tip < 1: # We're in the money lads
                            print("Gametime: " + str(converted_date))
                            print("Team1: " + str(i[3]) + " on " + str(i[0]) + " with odds: " + str(i[1]))
                            print("Team2: " + str(j[4]) + " on " + str(j[0]) + " with odds: " + str(j[2]))
                            if sport == 'soccer':
                                print("Draw on " + str(j[0]) + " with odds: " + str(j[2]))
                            print("Total Implied Prob: " + str(tip))
                            print('\n')
