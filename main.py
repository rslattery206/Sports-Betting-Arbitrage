import requests
import pytz
import pickle
from datetime import datetime, timedelta
from arbitrage_classes import ArbitrageManager, ArbitrageOpportunity


# 279c7cb0a5d77305c981038882f61408
# 462642ce457fcd2071b969b5387e89a4


def get():
    possible_sports = ['americanfootball_ncaaf',
                       'americanfootball_nfl',
                       'americanfootball_nfl_super_bowl_winner',
                       'aussierules_afl', 'baseball_mlb', 'basketball_nba',
                       'cricket_test_match', 'golf_masters_tournament_winner',
                       'golf_the_open_championship_winner', 'golf_us_open_winner',
                       'icehockey_nhl', 'mma_mixed_martial_arts', 'rugbyleague_nrl',
                       'soccer_australia_aleague', 'soccer_brazil_campeonato',
                       'soccer_denmark_superliga', 'soccer_finland_veikkausliiga',
                       'soccer_japan_j_league', 'soccer_league_of_ireland',
                       'soccer_norway_eliteserien', 'soccer_spain_segunda_division',
                       'soccer_sweden_allsvenskan', 'soccer_sweden_superettan',
                       'soccer_uefa_european_championship', 'soccer_usa_mls',
                       'tennis_atp_french_open', 'tennis_wta_french_open']
    possible_sports = ['americanfootball_ncaaf',
                       'americanfootball_nfl',
                       'americanfootball_nfl_super_bowl_winner',
                       'aussierules_afl', 'baseball_mlb', 'basketball_nba',
                       'cricket_test_match', 'golf_masters_tournament_winner',
                       'golf_the_open_championship_winner', 'golf_us_open_winner',
                       'icehockey_nhl', 'mma_mixed_martial_arts']

    response_json_list = []
    for given_sport in possible_sports:
        print(given_sport)
        key = '279c7cb0a5d77305c981038882f61408'
        mkt = 'h2h'
        region = 'us'
        params = {'apiKey': key, 'region': region, 'mkt': mkt}
        url = f'https://api.the-odds-api.com/v4/sports/' \
              f'{given_sport}/odds/' \
              f'?apiKey={key}' \
              f'&regions={region}' \
              f'&markets={mkt}'
        response_given_sport = requests.get(url, params=params)
        if response_given_sport.status_code == 200:
            response_json_list.append(response_given_sport.json())
        else:
            print(response_given_sport.status_code)
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
    current_date = datetime.utcnow()
    pacific_tz = pytz.timezone(timezone_str)
    game_time_utc = pytz.utc.localize(parsed_date)
    converted_game_time = game_time_utc.astimezone(pacific_tz)
    future_threshold = current_date + timedelta(minutes=threshold)  # adds threshold to current time
    future_boolean = parsed_date > future_threshold
    return future_boolean, converted_game_time


def extract_bet_information(resp_json):
    # Extract bookie, sport, odds, team names, and game time.
    odds_list_inner = []
    bookmakers = resp_json[game_index]['bookmakers']
    sport = resp_json[game_index]['sport_key']
    for entry_index in range(0, len(bookmakers)):
        title = bookmakers[entry_index]['title']
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
                                "sport_key": sport})
    return odds_list_inner


if __name__ == '__main__':
    responses = get()
    arbitrage_manager = ArbitrageManager()
    for resp in responses:  # for all sports
        for game_index in range(0, len(resp)):  # for all games in that sport

            # Only consider games that haven't begun.
            is_future, converted_date = check_if_future_game(resp[game_index]['commence_time'], 30)

            if is_future:
                odds_list = extract_bet_information(resp)
                for i in odds_list:
                    for j in odds_list:
                        if i != j:

                            max_draw_price = max(i["draw_price"], j["draw_price"])
                            t1p = i["team1_price"]
                            t2p = j["team2_price"]
                            tip = total_implied_prob(t1p, t2p, max_draw_price)
                            if tip < 1:  # We're in the money lads
                                gametime = i["time"]
                                sport = str(i["sport_key"])
                                team1 = str(i["team1_name"])
                                team2 = str(j["team2_name"])
                                bookmaker1 = str(i["title"])
                                bookmaker2 = str(j["title"])
                                odds1 = i["team1_price"]
                                odds2 = j["team2_price"]
                                draw_odds = j["draw_price"] if j["draw_price"] > 0 else None
                                opportunity = ArbitrageOpportunity(gametime, sport, team1, team2, bookmaker1,
                                                                   bookmaker2, odds1, odds2, draw_odds)
                                arbitrage_manager.add_opportunity(opportunity)

    # all loops have now ended
    print(arbitrage_manager.print_opportunities())
    # with open('arbitrage_manager.pk1', 'wb') as file:
    #     pickle.dump(arbitrage_manager, file)

