import urllib.request
from bs4 import BeautifulSoup
import json
from datetime import datetime

# NOTE: IN ORDER FOR THIS APP TO WORK, YOUR STEAM WISHLIST MUST BE SET TO PUBLIC

# If this is the case, enter your Steam ID below to continue
# (Your Steam ID can be found by logging into Steam, clicking on your profile, and then "account details")

STEAM_ID = 'Anteaterman23'

# Cache settings
# (For efficiency, this program will create a cache, with the specified filename, to store information that it fetches)
# (It will only fetch and store new data if the timeout has expired, which is measured in seconds, or if the steam id changes)

CACHE_FILENAME = 'steam_wishlist_cache.txt'
CACHE_TIMEOUT_SECS = 50000

# Constants (do not modify these unless the app is malfunctioning)

WISHLIST_STEM_NUM = "https://store.steampowered.com/wishlist/profiles/"
WISHLIST_STEM_STR = "https://store.steampowered.com/wishlist/id/"
APP_STEM = "https://store.steampowered.com/app/"
ALLOWED_SPECIAL_CHARS = [' ', '\'', ':', '.', '-', '/', '|', '%']
EPSILON = 2000


# --------------------------------------------------------------------------- #

# Helper Functions: Web Scraping

def make_soup_string(url, encode_utf=True):
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')
    if encode_utf:
        return str(soup.prettify().encode('utf-8'))
    else:
        return str(soup.prettify())

def is_unavailable(soup_str):
    availability_tag = 'is no longer available on the Steam store'
    return availability_tag in soup_str

def is_unreleased(soup_str):
    unreleased_tag_1 = 'This game is not yet available on Steam'
    unreleased_tag_2 = 'Pre-purchase'
    return unreleased_tag_1 in soup_str or unreleased_tag_2 in soup_str

def is_on_sale(soup_str, app_name=None):
    if app_name is None:
        app_name_start_index = soup_str.find('<title>') + 9
        app_name_end_index = soup_str.find('on Steam')

        app_name = soup_str[app_name_start_index:app_name_end_index].strip()
        app_name = ''.join(char for char in app_name if char.isalnum() or char in ALLOWED_SPECIAL_CHARS)
        
    for num in range(1,101):
        discount_tag = 'Save ' + str(num) + '% on '
        if discount_tag in app_name:
            return True
    return False

def extract_title(soup_str):
    app_name_start_index = soup_str.find('<title>') + 9
    app_name_end_index = soup_str.find('on Steam')

    app_name = soup_str[app_name_start_index:app_name_end_index].strip()
    app_name = ''.join(char for char in app_name if char.isalnum() or char in ALLOWED_SPECIAL_CHARS)
    
    # Edge case: If game is on sale, remove the "Save xx% on" prefix
    if is_on_sale(soup_str, app_name=app_name):
        percent_index = app_name.find('%')
        return str(app_name[percent_index+5:].encode("utf-8"))[2:-1]
    return str(app_name.encode("utf-8"))[2:-1]

def extract_price(soup_str):
    if not is_on_sale(soup_str):
        game_start_index = soup_str.find('class="game_purchase_price price"') + 10
        
        # If no price is found, must be free
        if game_start_index == 9:
            return float(0)
        
        price_start_index = soup_str.find('$', game_start_index) + 1
        
        # If price listed is for a different item, must be free
        if price_start_index - game_start_index > EPSILON:
            return float(0)
        
        price_end_index = soup_str.find('<', price_start_index)
        try:
            return float(soup_str[price_start_index:price_end_index].strip())
        except ValueError:
            return float(0)
    
    else:
        discount_start_index = soup_str.find('class="discount_final_price"') + 10
        
        price_start_index = soup_str.find('$', discount_start_index) + 1
        price_end_index = soup_str.find('<', price_start_index)
        try:
            return float(soup_str[price_start_index:price_end_index].strip())
        except ValueError:
            return float(0)
        
def extract_first_number(str, start_index):
    res = ""
    begin_record = False
    
    for char in str[start_index:]:
        if char.isnumeric():
            begin_record = True
        if begin_record:
            if char.isnumeric():
                res += char
            else:
                break
        
    return int(res)

# Helper Functions: Bonuses

def extract_review_bonus(soup_str):
    review_html_tag = "nonresponsive_hidden responsive_reviewdesc"
    
    review_alltime_index = soup_str.find(review_html_tag)
    review_percent_alltime = extract_first_number(soup_str, review_alltime_index)
    
    review_recent_index = soup_str.find(review_html_tag, review_alltime_index+10)
    if review_recent_index > 0:
        review_percent_recent = extract_first_number(soup_str, review_recent_index)
    else:
        review_percent_recent = review_percent_alltime
    
    return (review_percent_alltime + review_percent_recent) / 200
    
def get_price_bonus(wishlist_item):
    price = wishlist_item["price"]
    
    thresholds = [
        (49.99, 0.25),
        (39.99, 0.4),
        (29.99, 0.45),
        (24.99, 0.5),
        (19.99, 0.6),
        (14.99, 0.7),
        (9.99, 0.8),
        (4.99, 0.9),
        (2.49, 0.95)
    ]
    for threshold, bonus in thresholds:
        if price >= threshold:
            return bonus
    return 1


# Helper Functions: Caching

def read_from_cache():
    try:
        with open(CACHE_FILENAME, 'r') as file:
            contents = file.read()
            
            id_index = contents.find('\n')
            id_str = contents[:id_index]
            if id_str != str(STEAM_ID):
                return None
            
            timestamp_index = contents.find('\n', id_index+1)
            timestamp_str = contents[id_index+1:timestamp_index]
            timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            timedelta = datetime.now() - timestamp_datetime
            if timedelta.seconds < CACHE_TIMEOUT_SECS:
                return contents[timestamp_index:]
            else:
                return None

    except FileNotFoundError:
        return None

def write_to_cache(wishlist):
    with open(CACHE_FILENAME, 'w') as file:
        file.write(str(STEAM_ID) + '\n')
        file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
        
        for item in wishlist:
            should_buy = '* ' if item["weight"] >= 90 else ''
            file.write(f'{should_buy} Game: {item["title"]} | Price: ${item["price"]} | Weight: {item["weight"]} {should_buy}\n')

# Helper Functions: Miscellaneous

def numeric_profile():
    return isinstance(STEAM_ID, int) or STEAM_ID.isnumeric()
        
# --------------------------------------------------------------------------- #

# Main Program

# Reading from cache
cache = read_from_cache()
if cache is not None:
    print(cache)
    exit(0)

# Web-scraping the Steam wishlist page
wishlist_page = WISHLIST_STEM_NUM + str(STEAM_ID) if numeric_profile() else WISHLIST_STEM_STR + STEAM_ID
soup_str = make_soup_string(wishlist_page)

# Extracting the wishlist as a JSON object
wishlist_start_index = soup_str.find('g_rgWishlistData')

wishlist_str = ''
shouldAddToArray = False
shouldBreak = False

for i in range(wishlist_start_index, len(soup_str)):
    char = soup_str[i]
    
    if char == '[':
        shouldAddToArray = True
    if char == ']':
        shouldBreak = True
    if shouldAddToArray:
        wishlist_str += char
    if shouldBreak:
        break

wishlist_json = json.loads(wishlist_str)
valid_wishlist_json = []

# Extracting appid information from JSON and web-scraping for title and sale price

for i in range(0, len(wishlist_json)):
    item = wishlist_json[i]
    
    appid = str(item['appid'])
    app_url = APP_STEM + appid
    soup_str = make_soup_string(app_url, encode_utf=False)
    
    # Not interested in items which are unavailable, unreleased, or free
    if is_unavailable(soup_str) or is_unreleased(soup_str) or extract_price(soup_str) == 0.0:
        continue
    
    valid_wishlist_json.append(dict())
    valid_wishlist_json[-1]["priority"] = item["priority"]
    valid_wishlist_json[-1]["title"] = extract_title(soup_str)
    valid_wishlist_json[-1]["price"] = extract_price(soup_str)
    valid_wishlist_json[-1]["review_bonus"] = extract_review_bonus(soup_str)
    print("Finished analyzing: " + valid_wishlist_json[-1]["title"])
    
# Weighting every wishlist item

highest_priority = len(valid_wishlist_json)-1

for item in valid_wishlist_json:    
    priority_factor = 0.5
    if item["priority"] > 0 and highest_priority > 0:
        priority_factor = (highest_priority - item["priority"]) / highest_priority
    
    review_factor = item["review_bonus"]
    pricing_factor = get_price_bonus(item)
    
    item["weight"] = min(max(round(48*priority_factor + 41*pricing_factor + 11*review_factor), 0), 100)

# Sort wishlist, then print and cache

sorted_wishlist = sorted(valid_wishlist_json, key=lambda x: x["weight"])
sorted_wishlist.reverse()

write_to_cache(sorted_wishlist)
print(read_from_cache())