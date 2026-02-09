#!/usr/bin/env python
import sys
import os

# Check Python version
if sys.version_info < (3, 6):
    print("Error: This script requires Python 3.6 or higher.")
    print(f"You are running Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("\nPlease install Python 3.6 or higher from https://www.python.org/downloads/")
    sys.exit(1)

# Check for required packages
missing_packages = []

try:
    import tkinter as tk
except ImportError:
    missing_packages.append("tkinter")

try:
    import requests
except ImportError:
    missing_packages.append("requests")

try:
    import pandas as pd
except ImportError:
    missing_packages.append("pandas")

try:
    from astral import LocationInfo
    from astral.sun import sun
except ImportError:
    missing_packages.append("astral")

if missing_packages:
    print("Error: Missing required packages!")
    print("\nThe following packages are not installed:")
    for package in missing_packages:
        print(f"  - {package}")
    
    print("\nTo install the missing packages, run:")
    if "tkinter" in missing_packages:
        print("\nFor tkinter:")
        print("  - On Mac: tkinter usually comes with Python")
        print("  - On Windows: tkinter usually comes with Python")
        print("  - On Linux: sudo apt-get install python3-tk")
    
    install_cmd = [pkg for pkg in missing_packages if pkg != "tkinter"]
    if install_cmd:
        print(f"\nFor other packages:")
        print(f"  pip install {' '.join(install_cmd)}")
    
    sys.exit(1)

from datetime import datetime, timedelta

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Split on first = only
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        pass  # .env file is optional

load_env_file()


class DayType:
    def __init__(self, start_swim, end_swim):
        self.start = start_swim
        self.end = end_swim


class QueryType:
    def __init__(self, start_date, num_days, interval='10', datum='MSL'):
        self.start = start_date
        self.num_days = num_days
        self.interval = interval
        self.datum = datum

    def query_niwa(self, swim_beach):
        url = 'https://api.niwa.co.nz/tides/data'
        apikey = os.getenv('NIWA_API_KEY')
        if not apikey:
            raise ValueError("NIWA_API_KEY environment variable not set. Please create a .env file or set the environment variable.")
        # Clean the API key of any whitespace or quotes
        apikey = apikey.strip().strip('"').strip("'")
        params = dict(lat=swim_beach.lat,
                      long=swim_beach.long,
                      datum=self.datum,
                      apikey=apikey,
                      startDate=self.start,
                      numberOfDays=self.num_days,
                      interval=self.interval
                      )
        return requests.get(url, params)


class Beach:
    def __init__(self, lat, long, good_height):
        self.lat = lat
        self.long = long
        self.good = good_height


def get_sunrise_sunset(lat, lng, date_obj):
    """
    Get sunrise and sunset times for a given location and date.
    
    Args:
        lat: Latitude as string or float
        lng: Longitude as string or float
        date_obj: datetime.date object
    
    Returns:
        Tuple of (sunrise_time_str, sunset_time_str) in HH:MM format
    """
    location = LocationInfo(latitude=float(lat), longitude=float(lng))
    s = sun(location.observer, date=date_obj)
    
    # Convert to Auckland timezone and format as HH:MM
    sunrise_auckland = s['sunrise'].astimezone(pd.Timestamp.now(tz='Pacific/Auckland').tz)
    sunset_auckland = s['sunset'].astimezone(pd.Timestamp.now(tz='Pacific/Auckland').tz)
    
    sunrise_str = sunrise_auckland.strftime('%H:%M')
    sunset_str = sunset_auckland.strftime('%H:%M')
    
    return sunrise_str, sunset_str


def swim_time_message(start, end):
    return ('On ' + start.strftime('%a %d %b') +
            ' Swimming should be good from ' +
            start.strftime('%X')[:5] +
            ' to ' +
            end.strftime('%X')[:5] +
            '.\n'
            )


def display_swim_times():
    message.insert(1.0, 'Have fun at ' + sw_beach.get() + ' beach!\n')


def swim_times(day, num_days='1'):
    swim_ = datetime.today()
    if day == 'tomorrow':
        swim_ = swim_ + timedelta(days=1)
    
    # Store the base date as a date object for astral
    base_date = swim_.date() if isinstance(swim_, datetime) else swim_
    swim_ = swim_.strftime('%Y-%m-%d')
    today_swim_request = QueryType(swim_, num_days)

    swim_day_type = times[sw_time.get()]['daytype']
    
    # Get the beach location for sunrise/sunset calculations
    current_beach = beach_dict[sw_beach.get()]

    r = today_swim_request.query_niwa(current_beach)
    
    # Check if the API request was successful
    if r.status_code != 200:
        error_msg = f'API Error: Status {r.status_code}\n'
        try:
            error_data = r.json()
            if 'message' in error_data:
                error_msg += f"Message: {error_data['message']}\n"
            else:
                error_msg += f"Response: {error_data}\n"
        except:
            error_msg += f"Response: {r.text}\n"
        message.insert(1.0, error_msg)
        return
    
    # Check if response has the expected data
    response_data = r.json()
    if 'values' not in response_data:
        error_msg = f'API Error: Unexpected response format\n'
        error_msg += f'Response: {response_data}\n'
        message.insert(1.0, error_msg)
        return
    
    df = pd.json_normalize(response_data['values']).set_index('time')
    df.index = pd.to_datetime(df.index).tz_convert('Pacific/Auckland')
    df['high_enough_tide'] = df['value'] > current_beach.good

    # Collect all messages in a list to display in correct order
    messages = []
    
    for i in range(int(num_days)):
        # Get actual sunrise/sunset for this specific day
        current_date = base_date + timedelta(days=i)
        sunrise_time, sunset_time = get_sunrise_sunset(current_beach.lat, current_beach.long, current_date)
        
        # Use actual sunrise/sunset times or the user's preferred time window
        if sw_time.get() == 'All Day':
            start_time_str = sunrise_time
            end_time_str = sunset_time
        elif sw_time.get() == 'Sneaky Morning Swim':
            start_time_str = sunrise_time
            end_time_str = swim_day_type.end
        elif sw_time.get() == 'After Work':
            start_time_str = swim_day_type.start
            end_time_str = sunset_time
        else:
            # Fallback to defined times
            start_time_str = swim_day_type.start
            end_time_str = swim_day_type.end
        
        start_swim_time = pd.Timestamp(current_date.strftime('%Y-%m-%d') + ' ' + start_time_str, tz='Pacific/Auckland')
        end_swim_time = pd.Timestamp(current_date.strftime('%Y-%m-%d') + ' ' + end_time_str, tz='Pacific/Auckland')

        # Get the data for this day's swim window
        day_data = df[start_swim_time:end_swim_time]['high_enough_tide']
        
        if day_data.sum() > 0:
            # Find continuous windows where tide is high enough
            # Create groups of consecutive True values
            tide_good = day_data.astype(int)
            # Find where tide changes from bad to good or good to bad
            tide_changes = tide_good.diff().fillna(0)
            
            # Find all continuous windows
            windows = []
            window_start = None
            
            for idx, val in day_data.items():
                if val and window_start is None:
                    # Start of a good window
                    window_start = idx
                elif not val and window_start is not None:
                    # End of a good window
                    windows.append((window_start, prev_idx))
                    window_start = None
                prev_idx = idx
            
            # If we ended with a good window still open, close it
            if window_start is not None:
                windows.append((window_start, prev_idx))
            
            # Generate messages for each window
            if len(windows) == 1:
                m = swim_time_message(windows[0][0], windows[0][1])
            elif len(windows) > 1:
                m = 'On ' + start_swim_time.strftime('%a %d %b') + ' swimming should be good:\n'
                for i, (win_start, win_end) in enumerate(windows, 1):
                    m += f'  Window {i}: {win_start.strftime("%H:%M")} to {win_end.strftime("%H:%M")}\n'
            else:
                m = 'On '+ start_swim_time.strftime('%a %d %b') +' no good time for swimming :(\n'
        else:
            m = 'On '+ start_swim_time.strftime('%a %d %b') +' no good time for swimming :(\n'

        messages.append(m)

    # Add header message
    if day == 'today':
        header = 'Have fun at ' + sw_beach.get() + ' beach today!\n'
    elif day == 'tomorrow':
        header = 'Have fun at ' + sw_beach.get() + ' beach tomorrow!\n'
    else:
        header = 'Swim times for ' + sw_beach.get() + ' beach over the next ' + num_days + ' days:\n\n'
    
    # Insert header first, then messages in ascending chronological order
    message.insert(1.0, header)
    for m in messages:
        message.insert('end', m)

def today_swim_times():
    swim_times('today')


def tomorrow_swim_times():
    swim_times('tomorrow')


def future_swim_report():
    swim_times('future', '14')

def clear_output():
    message.delete(1.0, 'end')

# Load beaches from CSV file
try:
    beaches_df = pd.read_csv('beaches.csv')
    beach_dict = {}
    for _, row in beaches_df.iterrows():
        beach_dict[row['beach']] = Beach(
            lat=str(row['lat']),
            long=str(row['long']),
            good_height=row['good_height']
        )
    beaches = list(beach_dict.keys())
except FileNotFoundError:
    print("Error: beaches.csv file not found!")
    print("Please make sure beaches.csv is in the same directory as this script.")
    sys.exit(1)
except Exception as e:
    print(f"Error reading beaches.csv: {e}")
    print("Please check that beaches.csv is properly formatted.")
    sys.exit(1)

times = {'All Day': {'daytype': DayType('08:00', '19:30'), 'dayname': "All Day"},
         'Sneaky Morning Swim': {'daytype': DayType('08:00', '08:30'), 'dayname': "Sneaky Morning Swim"},
         'After Work': {'daytype': DayType('16:00', '19:30'), 'dayname': "After Work"}}

# Note: Sunrise and sunset times are now calculated dynamically using the astral library
# The times above are fallback values or user-defined time preferences for morning/after work swims

# Setting up the gui program
gui = tk.Tk()
gui.title("Fun Times Tides")
gui.geometry("500x500")

sw_beach = tk.StringVar(gui)
sw_beach.set(list(beach_dict.keys())[0])
sw_time = tk.StringVar(gui)
sw_time.set(list(times.keys())[0])

beach_selector = tk.OptionMenu(gui, sw_beach, *beaches)
beach_selector.pack()

time_selector = tk.OptionMenu(gui, sw_time, *list(times.keys()))
time_selector.pack()

# button = tk.Button(gui, text='When is it good to swim?', command=display_swim_times)
# button.pack()

swim_today = tk.Button(gui, text='Can I swim today?', command=today_swim_times)
swim_today.pack()

swim_tomorrow = tk.Button(gui, text='Can I swim tomorrow?', command=tomorrow_swim_times)
swim_tomorrow.pack()

future_swim = tk.Button(gui, text='When can I swim in the next 2 weeks?', command=future_swim_report)
future_swim.pack()

clear_button = tk.Button(gui, text='Clear Output', command=clear_output)
clear_button.pack()

message = tk.Text(gui, width=200, height=70)
message.pack()

gui.mainloop()
