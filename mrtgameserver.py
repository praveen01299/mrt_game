from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import random
from geopy.distance import great_circle
import json

# Load station data from JSON file
with open('mrt_stations.json', 'r') as f:
    MRT_Stations = json.load(f)

game_state = {'is_playing': False, 'correct_answer': None, 'attempts': 0}

def find_station(station_name, MRT_Stations):
    for station in MRT_Stations:
        if station['Station_Name'].lower() == station_name.lower():
            return station
    return None

def get_direction(user_location, correct_location):
    lat_diff = correct_location[0] - user_location[0]
    lon_diff = correct_location[1] - user_location[1]
    direction = "towards the "

    if lat_diff > 0:
        direction += "north"
    elif lat_diff < 0:
        direction += "south"

    if lon_diff > 0:
        direction += " east"
    elif lon_diff < 0:
        direction += " west"

    return direction

def compare_stations(correct_station, user_station):
    correct_location = tuple(map(float, correct_station['Location'].split(',')))
    user_location = tuple(map(float, user_station['Location'].split(',')))

    distance = great_circle(correct_location, user_location).kilometers
    direction = get_direction(user_location, correct_location)

    if correct_station['Station_Name'].lower() == user_station['Station_Name'].lower():
        return "Correct Answer!", True

    same_line = set(correct_station['Line']).intersection(set(user_station['Line']))
    if same_line:
        response = "Correct Line"
    else:
        response = "Wrong Line"

    # Fix for comparing the year of operation:
    if correct_station['Year_Started_Operation'] < user_station['Year_Started_Operation']:
        age_response = "The correct answer is an older station"
    elif correct_station['Year_Started_Operation'] > user_station['Year_Started_Operation']:
        age_response = "The correct answer is a newer station"
    else:
        age_response = "Correct Age"

    return f"{response}. {age_response}. Distance: {distance:.2f} km {direction}.", False

# 🔁 Updated all functions below to async and updated context types
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome to the MRT Station Guessing Game! Type /start_game to begin.')

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global game_state
    game_state['is_playing'] = True
    game_state['correct_answer'] = random.choice(MRT_Stations)
    game_state['attempts'] = 0

    map_url = 'https://dam.mediacorp.sg/image/upload/s--kikA5vSH--/f_auto,q_auto/v1/mediacorp/cna/image/2023/01/18/MRT%20map.png?itok=BkwVTtKV'  # Your MRT map image link

    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=map_url)
    await update.message.reply_text("One of the 134 MRT Stations is the correct answer! Can you figure out which one it is? Type your guess below, or type /exit to give up.")

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global game_state
    if not game_state['is_playing']:
        await update.message.reply_text("No game is currently active. Use /start_game to begin a new game.")
        return

    user_guess = update.message.text
    user_station = find_station(user_guess, MRT_Stations)

    if not user_station:
        await update.message.reply_text("There's no such station! Try again.")
        return

    game_state['attempts'] += 1
    correct_station = game_state['correct_answer']
    result, correct = compare_stations(correct_station, user_station)
    await update.message.reply_text(result)

    if correct:
        await update.message.reply_text(f"🎉 Congratulations! You found it in {game_state['attempts']} attempts. Type /start_game to play again.")
        game_state['is_playing'] = False
    else:
        await update.message.reply_text("Try again or type /exit to give up.")

async def exit_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global game_state
    if game_state['is_playing']:
        await update.message.reply_text(
            f"You gave up after {game_state['attempts']} attempts. The correct station was {game_state['correct_answer']['Station_Name']}."
        )
        game_state['is_playing'] = False
    else:
        await update.message.reply_text("No game is currently active. Use /start_game to begin a new game.")

def main():
    TOKEN = 'INPUT TOKEN HERE'
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_game", start_game))
    app.add_handler(CommandHandler("exit", exit_game))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    app.run_polling()

if __name__ == '__main__':
    main()  
