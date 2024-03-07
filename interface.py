import pickle
import tkinter as tk
from tkinter import ttk
import pygame

def load_persistent():
    with open('persistent.pk1', 'rb') as file:
        try:
            return pickle.load(file)
        except EOFError:
            pass

def play_sound():
    sound = pygame.mixer.Sound('sound.wav')
    sound.play()
    sound.set_volume(0.1)

def update_display():
    current_data = load_persistent()

    # Check if there's a change in data
    if hasattr(update_display, 'previous_data') and update_display.previous_data != current_data:
        play_sound()

    update_display.previous_data = current_data  # Save the current data for the next comparison

    tree.delete(*tree.get_children())  # Clear previous content

    for combination, value in current_data.items():
        lifespan1, lifespan2 = value[-2:]
        profit1, profit2 = combination.get_expected_profits()
        # Display the row in the Treeview
        item_id = tree.insert('', 'end', values=(
            combination.gametime,
            combination.sport,
            round(1 - combination.total_implied_prob, 4),
            combination.team1,
            combination.team2,
            combination.bookmaker1,
            combination.bookmaker2,
            combination.bet1,
            combination.bet2,
            round(profit1, 2),
            round(profit2, 2),
            lifespan1,
            lifespan2
        ))

        # Add a button next to each row
        tree.item(item_id, tags=('button',))

    root.after(1000, update_display)  # Update every 1000 milliseconds (1 second)

def on_click(event):
    print("onclick")
    # item_id = tree.identify_row(event.y)
    # item_values = tree.item(item_id, 'values')
    # sport = item_values[1]
    # team1 = item_values[3]
    # team2 = item_values[4]
    # teams = [team1, team2]
    # bookmaker1 = item_values[5]
    # bookmaker2 = item_values[6]
    # print('selecting the first bet now')
    # select_bet(teams, team1, bookmaker1, sport)
    # print('now selecting the second bet')
    # select_bet(teams, team2, bookmaker2, sport)

if __name__ == "__main__":
    pygame.init()

    root = tk.Tk()
    d = {}
    root.title("Ryan's Nice Viewer")
    root.geometry("800x400")
    columns = ['Game Time', 'Sport', 'Margin', 'Team 1', 'Team 2', 'Book1', 'Book2',
               'Bet1', 'Bet2', 'Profit1', 'Profit2', 'Life1', 'Life2']

    tree = ttk.Treeview(root, columns=columns, show='headings', height=10)
    tree.pack(pady=10)

    # Add column headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=50)

    # Add an event handler for clicks on the treeview
    tree.bind('<ButtonRelease-1>', on_click)

    # Initial update
    update_display()

    # Start the main loop
    root.mainloop()
