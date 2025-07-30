from lunardate import LunarDate
import datetime

def get_lunar_phase(date=None):
    """
    Calculate the current lunar phase based on the lunar calendar day.
    
    Args:
        date: A datetime.date object. If None, uses today's date.
        
    Returns:
        A string describing the current lunar phase with an emoji.
    """
    if not date:
        date = datetime.date.today()
    
    # Convert solar date to lunar date and get the day of lunar month
    moon_day = LunarDate.fromSolarDate(date.year, date.month, date.day).day
    
    # Determine the lunar phase based on the day of the lunar month
    if moon_day == 1:
        return 'New Moon 🌑'
    elif 2 <= moon_day <= 7:
        return 'Waxing Crescent 🌒'
    elif moon_day == 8:
        return 'First Quarter 🌓'
    elif 9 <= moon_day <= 14:
        return 'Waxing Gibbous 🌔'
    elif moon_day == 15:
        return 'Full Moon 🌕'
    elif 16 <= moon_day <= 21:
        return 'Waning Gibbous 🌖'
    elif moon_day == 22:
        return 'Last Quarter 🌗'
    else:  # 23-30
        return 'Waning Crescent 🌘'