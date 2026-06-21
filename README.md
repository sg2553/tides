# Fun Times Tides - Swimming Tide Checker

A Python application to check when tide conditions are good for swimming at various Auckland beaches.

## Setup Instructions

### 1. Install Python
- **Mac**: Python usually comes pre-installed. Check by running `python3 --version`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### 2. Install Required Packages
Open your terminal (Mac) or command prompt (Windows) and run:
```bash
pip install requests pandas astral fpdf2
```

If you're using the project's conda environment, activate it first: `conda activate tides`

### 3. Set Up Your Files
Make sure all these files are in the same folder:
- `fun_times.py` (the main script)
- `beaches.csv` (beach data file)
- `.env` (your API key - see next step)

### 4. Set Up Your NIWA API Key

1. Copy `.env.example` to `.env`:
   - Mac/Linux: `cp .env.example .env`
   - Windows: `copy .env.example .env`
2. Open `.env` in a text editor
3. Replace `your_api_key_here` with your actual NIWA API key
4. Save the file

### 5. Get a NIWA API Key
If you don't have an API key yet, visit: https://api.niwa.co.nz/

### 6. Run the Application
```bash
python fun_times.py
```
or on Mac:
```bash
python3 fun_times.py
```

## How to Use

1. Select your beach from the dropdown menu
2. Choose your preferred swimming time (All Day, Sneaky Morning Swim, or After Work)
3. Click one of the buttons:
   - "Can I swim today?" - Check today's conditions
   - "Can I swim tomorrow?" - Check tomorrow's conditions
   - "Next 2 weeks" - Get a 14-day forecast

### Detailed PDF Report
For trip planning, you can generate a detailed PDF report instead:
1. Select your beach
2. Enter a start date (YYYY-MM-DD) and number of days (1-30) in the "Detailed Report" fields
3. Click "Generate Detailed Report"
4. Choose where to save the PDF in the dialog that appears

The report includes one page per day, with the tide height at every hour from 5:00 AM to 10:00 PM, plus sunrise/sunset times and the moon phase.

## Available Beaches
The app currently includes:
- Point Chevalier (Pt_Chev)
- Takapuna
- Muriwai
- Wenderholm
- Point Wells (Pt_Wells)
- Kaiteriteri

### Adding Your Own Beaches
You can add more beaches by editing `beaches.csv`. Each line should have:
- beach name (no spaces, use underscores)
- latitude
- longitude  
- minimum tide height in meters for good swimming

Example:
```csv
beach,lat,long,good_height
MyBeach,-36.123456,174.123456,0.5
```

## Notes
- The app checks tide height to determine good swimming conditions
- Each beach has different minimum tide height requirements
- Sunrise and sunset times are calculated automatically for each day using the astral library
- Times adjust based on your selected time preference (All Day uses actual sunrise/sunset)
- The detailed PDF report also shows the moon phase for each day, calculated with the astral library
