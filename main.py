import time

import requests
import pytz
import pickle
from datetime import datetime, timedelta, timezone
from arbitrage_classes import ArbitrageManager, ArbitrageOpportunity


def get(key_param, region_param, mkt_param):
    possible_sports = ['americanfootball_ncaaf',
                       'americanfootball_nfl',
                       'aussierules_afl',
                       'baseball_mlb',
                       'basketball_nba',
                       'cricket_test_match',
                       'icehockey_nhl',
                       'mma_mixed_martial_arts',
                       'rugbyleague_nrl',
                       'soccer_australia_aleague',
                       'soccer_brazil_campeonato',
                       'soccer_denmark_superliga',
                       'soccer_finland_veikkausliiga',
                       'soccer_japan_j_league',
                       'soccer_league_of_ireland',
                       'soccer_norway_eliteserien',
                       'soccer_spain_segunda_division',
                       'soccer_sweden_allsvenskan',
                       'soccer_sweden_superettan',
                       'soccer_uefa_european_championship',
                       'soccer_usa_mls',
                       'tennis_atp_french_open',
                       'tennis_wta_french_open']
    response_json_list = []
    for given_sport in possible_sports:
        key = key_param
        mkt = mkt_param
        region = region_param
        params = {'apiKey': key, 'region': region, 'mkt': mkt}
        url = f'https://api.the-odds-api.com/v4/sports/' \
              f'{given_sport}/odds/' \
              f'?apiKey={key}' \
              f'&regions={region}' \
              f'&markets={mkt}'
        response_given_sport = requests.get(url, params=params)
        if response_given_sport.status_code == 200:
            response_json_list.append(response_given_sport.json())
        # else:
        #     print(response_given_sport.status_code)
    return response_json_list


def total_implied_prob(price1, price2, draw):
    # Calculates total implied probability given decimal odds (price)
    if draw == 0:
        return (1 / price1) + (1 / price2)
    else:
        return (1 / price1) + (1 / price2) + (1 / draw)


def check_if_future_game(game_time_str, threshold, timezone_str='America/Los_Angeles'):
    # Checks that game starts more than (threshold) minutes in the future,
    # also returns game time converted to given timezone (default pacific)
    parsed_date = datetime.strptime(game_time_str, "%Y-%m-%dT%H:%M:%SZ")
    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
    current_date = datetime.now(timezone.utc)
    future_threshold = current_date + timedelta(minutes=threshold)  # adds threshold to current time
    future_boolean = parsed_date > future_threshold

    pacific_tz = pytz.timezone(timezone_str)
    converted_game_time = parsed_date.astimezone(pacific_tz)
    return future_boolean, converted_game_time


def extract_bet_information(resp_json, game_index, converted_date):
    # Extract bookie, sport, odds, team names, and game time.
    odds_list_inner = []
    bookmakers = resp_json[game_index]['bookmakers']
    sport = resp_json[game_index]['sport_key']
    for entry_index in range(0, len(bookmakers)):
        title = bookmakers[entry_index]['title']
        last_update = bookmakers[entry_index]['last_update']
        outcomes = bookmakers[entry_index]['markets'][0]['outcomes']
        team1_name = outcomes[0]['name']
        team1_price = outcomes[0]['price']
        team2_name = outcomes[1]['name']
        team2_price = outcomes[1]['price']

        draw1 = 0
        draw2 = 0
        if len(outcomes) == 3:  # draw possibility
            draw1 = outcomes[2]['price']
            draw2 = outcomes[2]['price']

        odds_list_inner.append({"title": title,
                                "team1_price": team1_price,
                                "team2_price": team2_price,
                                "team1_name": team1_name,
                                "team2_name": team2_name,
                                "time": str(converted_date),
                                "draw_price": min(draw1, draw2),
                                "sport_key": sport,
                                "last_update": last_update})
    return odds_list_inner


def get_bookie_blacklist():
    filepath = "bookieblacklist.txt"
    with open(filepath, "r") as file:
        lines = file.read().splitlines()
    return lines


def search(key, region, mkt, iteration_counter=0):
    bookie_blacklist = get_bookie_blacklist()
    unique_bookies = []
    responses = get(key, region, mkt)
    arbitrage_manager = ArbitrageManager()
    for resp in responses:  # for all sports
        for game_index in range(0, len(resp)):  # for all games in that sport

            # Only consider games that haven't begun.
            is_future, converted_date = check_if_future_game(resp[game_index]['commence_time'], 30)

            if is_future:
                odds_list = extract_bet_information(resp, game_index, converted_date)
                for i in odds_list:
                    for j in odds_list:
                        if i != j:
                            if i["title"] not in bookie_blacklist and j["title"] not in bookie_blacklist:
                                max_draw_price = max(i["draw_price"], j["draw_price"])
                                if i["draw_price"] > j["draw_price"]:
                                    best_draw_odds_bookie = i["title"]
                                else:
                                    best_draw_odds_bookie = j["title"]
                                t1p = i["team1_price"]
                                t2p = j["team2_price"]
                                tip = total_implied_prob(t1p, t2p, max_draw_price)
                                if tip < .99:  # We're in the money lads

                                    gametime = i["time"]
                                    sport = str(i["sport_key"])
                                    team1 = str(i["team1_name"])
                                    team2 = str(j["team2_name"])
                                    bookmaker1 = str(i["title"])
                                    bookmaker2 = str(j["title"])
                                    odds1 = i["team1_price"]
                                    odds2 = j["team2_price"]
                                    last_update1 = i["last_update"]
                                    last_update2 = j["last_update"]
                                    draw_odds = max_draw_price
                                    opportunity = ArbitrageOpportunity(gametime, sport, team1, team2, bookmaker1,
                                                                       bookmaker2, odds1, odds2, last_update1,
                                                                       last_update2, best_draw_odds_bookie,
                                                                       draw_odds)
                                    arbitrage_manager.add_opportunity(opportunity)
                                    unique_bookies.append(bookmaker1)

    # all loops have now ended
    arbitrage_manager.filter()
    arbitrage_manager.sort_opportunities()
    print(arbitrage_manager.print_opportunities())
    # dump to pk1
    with open(f'pickles/arbitrage_manager{iteration_counter}.pk1', 'wb') as file:
        pickle.dump(arbitrage_manager, file)


if __name__ == '__main__':
    key = "131888119516489dbac0468fe8a984d0"
    search(key, 'us', 'h2h')

