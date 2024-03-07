import pickle
import csv
import os
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from arbitrage_classes import ArbitrageManager, ArbitrageOpportunity


def load_pickle(filepath):
    with open(filepath, 'rb') as file:
        pickle_juice = pickle.load(file)
    return pickle_juice


def to_csv_row(opportunity):
    return [
        opportunity.recorded_time,
        str(opportunity.gametime + opportunity.team1 + opportunity.team2),
        str(opportunity.gametime + opportunity.team1 + opportunity.team2 +
            opportunity.bookmaker1 + opportunity.bookmaker2),
        opportunity.gametime,
        opportunity.sport,
        opportunity.team1,
        opportunity.team2,
        opportunity.bookmaker1,
        opportunity.bookmaker2,
        opportunity.odds1,
        opportunity.odds2,
        opportunity.draw_odds,
        opportunity.draw_odds_bookie,
        opportunity.total_implied_prob,
        opportunity.last_update1,
        opportunity.last_update2,
        opportunity.bet1,
        opportunity.bet2,
        opportunity.bet3
    ]


def generate_csv(identifier):
    try:
        files = os.listdir("pickles")
        filecount = len([p for p in files if os.path.isfile(os.path.join("pickles", p))])
    except Exception as e:
        print(f'Error while trying to generate CSV: {e}')
        return
    all_opps = []
    for i in range(0, filecount):
        data = load_pickle(f'pickles/arbitrage_manager{i}.pk1')
        arbitrage_manager = ArbitrageManager(data)
        opps = arbitrage_manager.get_opportunities()
        for o in opps:
            all_opps.append(o)

    with open(f"csv/opportunities{identifier}.csv", 'w', newline='') as file:
        csv_writer = csv.writer(file)
        header = ["Recorded Time", "MatchId", "ComboId", "Game Time", "Sport", "Team1", "Team2", "Bookmaker1",
                  "Bookmaker2", "Odds1", "Odds2", "Draw Odds", "Draw Odds Bookie",
                  "Total Implied Probability", "Last Update1", "Last Update2",
                  "Bet1", "Bet2", "Bet3"]
        csv_writer.writerow(header)
        for o in all_opps:
            csv_writer.writerow(to_csv_row(o))


def sql(query, csv_path):
    try:
        connection = sqlite3.connect('mydb.db')
        cursor = connection.cursor()
        cursor.execute(".open 'mydb.db'")
        cursor.execute(".mode csv")
        cursor.execute(f"import '{csv_path}' opps")
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
    except sqlite3.Error as e:
        print(f"SQLite3 error: {e}")
    except Exception as e:
        print(f"Broader exception while running SQL: {e}")


def fix_dates(identifier):
    updated_rows = []
    with open(f"csv/opportunities{identifier}.csv", 'r', newline='') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Convert the date strings in "Last Update1" and "Last Update2" columns to datetime objects
            last_update1 = datetime.strptime(row["Last Update1"], '%Y-%m-%dT%H:%M:%SZ')
            last_update2 = datetime.strptime(row["Last Update2"], '%Y-%m-%dT%H:%M:%SZ')
            row["Last Update1"] = last_update1.strftime('%Y-%m-%dT%H:%M:%SZ')
            row["Last Update2"] = last_update2.strftime('%Y-%m-%dT%H:%M:%SZ')
            updated_rows.append(row)

        # Write the updated data back to the CSV file
    with open(f"csv/opportunities{identifier}.csv", 'w', newline='') as file:
        fieldnames = updated_rows[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)


def group_csv(identifier):
    # Groups by ComboId, drops 0 lifespan opps
    df = pd.read_csv(f'csv/opportunities{identifier}.csv', encoding='latin-1')
    df["Lifespan1"] = pd.to_datetime(df["Last Update1"], format='%Y-%m-%dT%H:%M:%SZ')
    df["Lifespan2"] = pd.to_datetime(df["Last Update2"], format='%Y-%m-%dT%H:%M:%SZ')
    df = df.groupby(['Bookmaker1', 'Bookmaker2', 'Team1', 'Team2', "Odds1", "Odds2", "Total Implied Probability"]).agg({
        'Lifespan1': lambda x: max(x) - min(x),
        'Lifespan2': lambda x: max(x) - min(x),
        'Recorded Time': lambda x: min(x)})
    df = df[(df['Lifespan1'] != pd.Timedelta(0)) & (df['Lifespan2'] != pd.Timedelta(0))]
    df['Lifespan1'] = df['Lifespan1'].astype(str).map(lambda x: x[7:])
    df['Lifespan2'] = df['Lifespan2'].astype(str).map(lambda x: x[7:])
    df = df.reset_index()
    df.to_csv(f'csv/opportunities{identifier}grouped.csv', index=False)


def combine_grouped():
    folder = "csv"
    combined = pd.DataFrame()
    for file in os.listdir(folder):
        if file.endswith(".csv") and "grouped" in file:
            path = os.path.join(folder, file)
            combined = pd.concat([combined, pd.read_csv(path)], ignore_index=True)
    return combined  # pandas dataframe


def clear_pickles():
    if os.path.exists("pickles"):
        print("Found " + str(len(os.listdir('pickles'))) + " pickles")
        user_input = input("Are you sure? Type yes and enter\n")
        if user_input == "yes":
            for filename in os.listdir("pickles"):
                file_path = os.path.join("pickles", filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
            print("Cleared pickles")
        else:
            print("Didn't clear pickles")
    else:
        print("No pickles directory")


if __name__ == '__main__':
    clear_pickles()
    # df = pd.read_csv("csv/opportunities1grouped.csv")
    # df2 = pd.read_csv("csv/opportunities2grouped.csv")
    # df = pd.concat([df, df2], ignore_index=True)
    # print(type(df["Lifespan1"][0]))
    # df.to_csv("csv/dookie.csv", index=False)
    #
    #
    # # df = combine_grouped()
    # df['Recorded Time'] = pd.to_datetime(df['Recorded Time'])
    # df['Date'] = df["Recorded Time"].dt.date
    # df['Date'] = df['Recorded Time'].dt.date
    # df['Day'] = df['Recorded Time'].dt.day_name()
    # df['Time'] = df['Recorded Time'].dt.time
    # df["Hour"] = df["Recorded Time"].dt.hour
    #
    # df['Lifespan1'] = pd.to_timedelta(df['Lifespan1'])
    # df['Lifespan1_minutes'] = (df['Lifespan1'] / pd.Timedelta(minutes=1)).astype(int)
    # df['Total Implied Probability'] = pd.to_numeric(df['Total Implied Probability'], errors='coerce')
    # print(type(df["Lifespan1"][0]))
    # # Plot 'Total Implied Probability' against 'Lifespan1'
    # plt.ylim(0.9, 1.0)
    # plt.xlim(0, 100)
    # plt.scatter(df['Lifespan1_minutes'], df['Total Implied Probability'])
    # plt.show()
