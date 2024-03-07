import requests
import pytz
import time
import pickle
import schedule
import subprocess
from datetime import datetime, timedelta, timezone
from arbitrage_classes import ArbitrageManager, ArbitrageOpportunity, Combination
import json


def get_single_sport(sport, key_param, region_param, mkt_param):
    key = key_param
    mkt = mkt_param
    region = region_param
    params = {'apiKey': key, 'region': region, 'mkt': mkt}
    url = f'https://api.the-odds-api.com/v4/sports/' \
          f'{sport}/odds/' \
          f'?apiKey={key}' \
          f'&regions={region}' \
          f'&markets={mkt}'
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json(), key
    else:
        newkey = delete_key(key)
        return get_single_sport(sport, newkey, region_param, mkt_param)


def get(key_param, region_param, mkt_param, soccer=True):
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
    if not soccer:
        possible_sports = [
            'americanfootball_ncaaf',
            'americanfootball_nfl',
            'baseball_mlb',
            'basketball_ncaab',
            'basketball_nba',
            'icehockey_nhl',
            'mma_mixed_martial_arts'
        ]
    response_json_list = []
    key = key_param
    for given_sport in possible_sports:
        resp_json, key_used = get_single_sport(given_sport, key, region_param, mkt_param)
        key = key_used
        response_json_list.append(resp_json)

    return response_json_list


def total_implied_prob(price1, price2, draw):
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
    future_threshold = current_date + timedelta(minutes=threshold)
    future_boolean = parsed_date > future_threshold

    pacific_tz = pytz.timezone(timezone_str)
    converted_game_time = parsed_date.astimezone(pacific_tz)
    return future_boolean, converted_game_time


def extract_bet_information(resp_json, game_index, converted_date):
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
        draw_price = 0
        if len(outcomes) == 3:  # draw possibility
            draw_price = outcomes[2]['price']

        odds_list_inner.append({"title": title,
                                "team1_price": team1_price,
                                "team2_price": team2_price,
                                "team1_name": team1_name,
                                "team2_name": team2_name,
                                "time": str(converted_date),
                                "draw_price": draw_price,
                                "sport_key": sport,
                                "last_update": last_update})
    return odds_list_inner


def read_bookie_whitelist():
    filepath = "bookiewhitelist.txt"
    with open(filepath, "r") as file:
        lines = file.read().splitlines()
    return lines


def read_bookie_blacklist():
    filepath = "bookieblacklist.txt"
    with open(filepath, "r") as file:
        lines = file.read().splitlines()
    return lines


def pickle_dump(identifier, arbitrage_manager):
    with open(f'pickles/arbitrage_manager{identifier}.pk1', 'wb') as file:
        pickle.dump(arbitrage_manager, file)


def pickle_dump_persistent(dictionary):
    # for persistent opportunities
    with open('persistent.pk1', 'wb') as file:
        pickle.dump(dictionary, file)


def read_keys():
    filepath = "keys.txt"
    with open(filepath, "r") as file:
        lines = file.read().splitlines()
    return lines


def read_links():
    filepath = "links.json"
    with open(filepath, "r") as file:
        dictionary = json.load(file)
    return dictionary


def delete_key(key):
    with open('keys.txt', 'r') as file:
        keys = read_keys()
        if key in keys:
            index = keys.index(key)
            keys.remove(key)
            with open('keys.txt', 'w') as keys_file:
                keys_file.write('\n'.join(keys))
            print("Deleted key " + str(key))
            # store_key(key, filename="spentkeys.txt")
            return keys[index]
        else:
            print("Key to be deleted was not found in the file.")


def time_difference(time1_str, time2_str):
    # returns time2 - time1 ~ (new - old)
    time_format = '%Y-%m-%dT%H:%M:%SZ'
    time1 = datetime.strptime(time1_str, time_format)
    time2 = datetime.strptime(time2_str, time_format)
    diff = time2 - time1
    return diff.total_seconds()


def seconds_to_time_str(secs):
    secs = int(secs)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    seconds = secs % 60
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)


def extract_school_name(team_name): # also exists in webinteraction
    # for ncaa
    words = team_name.split()
    if len(words) == 2:
        return words[0]
    else:
        return ' '.join(words[:2])


def opp_print(key, value):
    links = read_links()
    if key.sport == "americanfootball_ncaaf" or key.sport == "basketball_ncaab":
        team1 = extract_school_name(key.team1)
        team2 = extract_school_name(key.team2)
    else:
        team1 = key.team1
        team2 = key.team2
    print("-------------")
    print(f"T1/T2: {team1} / {team2}")
    print(f"Book1: {links[key.bookmaker1][key.sport]}")
    print(f"Book2: {links[key.bookmaker2][key.sport]}")
    print(f"Bet1:  {int(key.bet1)}")
    print(f"Bet2:  {int(key.bet2)}")
    print(
        f"T1/T2 Profits:{key.bet1 * key.odds1 - key.bet1 - key.bet2} / {key.bet2 * key.odds2 - key.bet1 - key.bet2}")
    print(f"T.I.P: {key.total_implied_prob}")
    print(f'Odds1/2: {key.odds1} / {key.odds2}')
    print(f'Lifespan 1/2: {seconds_to_time_str(value[2])} / {seconds_to_time_str(value[3])}')
    print("-------------\n")


def playsound():
    subprocess.run(["start", "/MIN", "sound.mp3"], shell=True)


def search(key, region, mkt, soccer=True, threshold=0.99):
    # Formally the main method
    bookie_blacklist = read_bookie_blacklist()
    bookie_whitelist = read_bookie_whitelist()
    responses = get(key, region, mkt, soccer)
    arbitrage_manager = ArbitrageManager()
    for resp in responses:  # for all sports
        for game_index in range(0, len(resp)):  # for all games in that sport
            is_future, converted_date = check_if_future_game(resp[game_index]['commence_time'], 0)
            if is_future:
                odds_list = extract_bet_information(resp, game_index, converted_date)
                for i in odds_list:
                    for j in odds_list:
                        if i != j:
                            if i["title"] not in bookie_blacklist and j["title"] not in bookie_blacklist:
                                max_draw_price = max(i["draw_price"], j["draw_price"])
                                if max_draw_price > 0:
                                    if i["draw_price"] > j["draw_price"]:
                                        best_draw_odds_bookie = i["title"]
                                    else:
                                        best_draw_odds_bookie = j["title"]
                                else:
                                    best_draw_odds_bookie = None
                                tip = total_implied_prob(i["team1_price"], j["team2_price"], max_draw_price)
                                if tip < threshold:
                                    recorded_time = datetime.now()
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
                                    opportunity = ArbitrageOpportunity(recorded_time, gametime, sport, team1, team2,
                                                                       bookmaker1, bookmaker2, odds1, odds2,
                                                                       last_update1, last_update2,
                                                                       best_draw_odds_bookie, max_draw_price)
                                    arbitrage_manager.add_opportunity(opportunity)

    # all loops have now ended
    # arbitrage_manager.filter()
    arbitrage_manager.sort_opportunities()
    return arbitrage_manager


def main():
    # parameters
    allow_soccer = False
    maxtip = .99
    interval_secs = 10
    #
    whitelist = read_bookie_whitelist()
    unique_combos = {}  # persistent opportunities are keys here, in the form of Combination class
    c = 0  # index of key
    iteration = 0

    while True:
        print("Iteration: " + str(iteration))
        key_list = read_keys()
        if len(key_list) == 0:
            print("No keys, aborting")
            break
        key = key_list[c]
        instance = search(key, 'us', 'h2h', allow_soccer, maxtip)
        # instance.print_opportunities()
        pickle_dump(iteration, instance)

        seen_combos = {}
        for o in instance.get_opportunities():
            seen_combos[Combination(o)] = [o.last_update1, o.last_update2, 0, 0]
        # delete combos from unique_combos that aren't in seen_combos. keys are combos
        for key in list(unique_combos.keys()):
            if key not in seen_combos:
                del unique_combos[key]

        # add new combos to unique combos
        for key, value in seen_combos.items():
            if key not in unique_combos:
                unique_combos[key] = value
            elif unique_combos[key][0] != seen_combos[key][0] or unique_combos[key][1] != seen_combos[key][1]:
                unique_combos[key][2] = time_difference(unique_combos[key][0], seen_combos[key][0])
                unique_combos[key][3] = time_difference(unique_combos[key][1], seen_combos[key][1])

        justplayed = False
        to_output = {}
        for key, value in unique_combos.items():  # value [2,3] = lifespans
            if key.bookmaker1 in whitelist and key.bookmaker2 in whitelist and key.bet1 < 30 and key.bet2 < 30 and (
                    value[2] > 0 and value[3] > 0):  # and (key.bookmaker1, key.bookmaker2) == ("Unibet", "FanDuel"):
                if not justplayed:
                    justplayed = True
                    # playsound()
                opp_print(key, value)
                to_output[key] = value
        pickle_dump_persistent(to_output)
        c += 1
        if c == len(key_list):
            c = 0
        iteration += 1
        time.sleep(interval_secs)


if __name__ == '__main__':
    # schedule.every().day.at("09:00").do(main)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
    main()
