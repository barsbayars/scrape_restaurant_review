import random
from playwright.sync_api import sync_playwright
import time
from playwright_stealth import stealth
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys

# Define data classes for Restaurant and RestaurantList

#Add coordinate + total number scraped 

@dataclass
class Review:
    """holds review data"""
    reviewer_name: str = None           #Reviewer's Name               eg.: John Smith
    reviewer_info: str = None           #Reviewer's Infomartion        eg.: Local Guide · 100 reviews · 50 photos
    review_lang: str = None             #Review Text Original Language eg.: 
    review_date: str = None             #Date reviewed                 eg.: 2 weeks ago
    rating: float = None                #Rating                        eg.: 5.0
    number_of_photos: int = None        #Number of photos posted       eg.: 2
    review_text: str = None             #Review Text                   eg.: This restaurant was nice
    

@dataclass
class Restaurant:
    """holds restaurant data"""
    s_key: str = None                                   #Search Key Word Used 
    name: str = None                                    #Restaurant Name
    category: str = None                                #Type of the restaurant
    # 0: No Price Range Listed 1:AED 1-50; 2: AED 50-100; 3: AED 100-150; 4: AED 150-200; 5:AED 200- 500; 6:AED 500+
    price: int = None                                   #Price range for the restaurant
    address: str = None                                 #Restaurant Address
    website: str = None                                 #Restaurant website if there is
    phone_number: str = None                            #Restaurant Phone Number    
    reviews_count: int = None                           #Total Restaurant Review
    reviews_average: float = None                       #Average Restaurant Rating eg.: 4.7
    latitude: float = None                              #Latitude
    longitude: float = None                             #Longtitude
    scraped_review_count: int = None                    #Total Scraped Review
    review_russian: int = None                          #Number of Russian Review
    review_other_l: int = None                          #Number of Reviews that are not English
    reviews: list[Review] = field(default_factory=list) #List of all scraped the Reviews (refer to class Review)

@dataclass
class RestaurantList:                                   #Big Guy that contains everything and creates csv file
    """holds list of Restaurant objects,
    and save to csv"""
    restaurant_list: list[Restaurant] = field(default_factory = list)
    save_at = 'output'

    def dataframe(self):
        """transform restaurant_list to pandas dataframe
        
        Returns: pandas data frame"""
        return pd.json_normalize(
            (asdict(restaurant) for restaurant in self.restaurant_list), sep="_"
        ) 

    def save_to_csv(self, filename):
        """Saves pandas dataframe to CSV file"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        file_path = f'{self.save_at}/{filename}.csv'
        if os.path.exists(file_path):
            self.dataframe().to_csv(file_path, mode='a', header=False, index=False)
        else:
            self.dataframe().to_csv(file_path, index=False)
#------------------------------------------------------------------------------------

# Helper function to extract coordinates from URL
def get_coordinates_from_url(url: str) -> tuple[float,float]:
    """helper function to extract coordinates from url just in case"""
    coordinates = url.split('/@')[-1].split('/')[0]
    #return lat, long
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])

# Function to get search list from arguments or input file
def get_search_list(args):
    if args.search:
        return [args.search]
    
    search_list = []
    input_file_name = 'input.txt'
    input_file_path = os.path.join(os.getcwd(), input_file_name)

    if os.path.exists(input_file_path):
        with open(input_file_path, 'r') as file:
            search_list = file.readlines()
    
    if len(search_list) == 0:
        print('Please either pass the -s search argument, or add searches to input.txt')
        sys.exit()
    
    return search_list

# Function to scrape listings from Google Maps
def scrape_listings(page, total):
    count = 0
    listings = []  # Initialize listings list
    while True:
        # Scroll to load more listings
        page.mouse.wheel(0, 10000)
        page.wait_for_timeout(3000)

        # Get the current number of listings
        new_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
        
        # If no new listings are loaded, break the loop
        if new_count == count:
            break
        
        count = new_count

        # Collect the listings
        listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
        listings = [listing.locator("xpath=..") for listing in listings]

        # Print the number of listings scraped so far
        print(f"Number of Restaurants Scraped: {len(listings)}")

        # If the total number of listings is reached, break the loop
        if len(listings) >= total:
            break

    print(f'Total Scraped: {len(listings)}')
    return listings

# Function to scrape reviews from the reviews section

def scrape_reviews(page, retries = 3):
    reviews = []
    review_russian = 0
    review_other_l = 0
    for attempt in range(retries):
        try:
            
            review_button = ""
            button ='//button[@data-tab-index="1"]'
            for i in '123':
                button = f'//button[@data-tab-index="{i}"]'
                review_button = page.locator(button).text_content(timeout=3000)
                if review_button == 'Reviews':
                    page.locator(button).click()  
                    page.wait_for_timeout(random.randint(2000,5000))
                    break
                else:
                    print(f'Review is not at {i} the button is {button}')
                    print(f'Text content from review button was {review_button}')

            

            # Scroll to load all reviews
            count = 0
            while True:
                page.mouse.wheel(0, 10000)
                page.wait_for_timeout(random.randint(2000,6000)) #Can I make time to wait random for each iteration in some range?
                new_count = page.locator('//div[@data-review-id]').count()
                if new_count == count:
                    break
                count = new_count

            print(f"Reviews scraped by scroll count: {count}")
            
            
            # Extract review information
            review_elements = page.locator('//div[@data-review-id]').all()
            for review_element in review_elements:
                reviewer_name_element = review_element.locator('//div[contains(@class, "d4r55")]')
                reviewer_info_element = review_element.locator('//div[contains(@class, "RfnDt ")]')
                review_lang_element = review_element.locator('//div[contains(@class, "oqftme")]')
                review_text_element = review_element.locator('//span[contains(@class, "wiI7pd")]')
                review_date_element = review_element.locator('//span[contains(@class, "rsqaWe")]')
                rating_element = review_element.locator('//span[contains(@class, "kvMYJc")]')
                number_of_photos_element = review_element.locator('//button[contains(@class, "KtCyie")]')

                reviewer_name = reviewer_name_element.text_content() if reviewer_name_element.count() > 0 else "N/A"
                reviewer_info = reviewer_info_element.text_content() if reviewer_info_element.count() > 0 else "N/A"
                review_lang = review_lang_element.text_content() if review_lang_element.count() > 0 else "English"
                review_text = review_text_element.text_content() if review_text_element.count() > 0 else "N/A"
                review_date = review_date_element.text_content() if review_date_element.count() > 0 else "N/A"
                rating = float(rating_element.get_attribute('aria-label').split()[0]) if rating_element.count() > 0 else "N/A"
                number_of_photos = len(number_of_photos_element.all()) if number_of_photos_element.count() > 0 else 0
                #Get the Original Language in the text
                
                if review_lang != "English":
                    review_lang = review_lang.split('(')[-1].split(')')[0]
                    if review_lang == "Russian":
                        review_russian += 1
                    review_other_l += 1

                    print(review_lang)

                #Felt like better to do it this way
                #Because I might get confused with the name etc
                reviews.append(Review(
                    reviewer_name=reviewer_name,
                    reviewer_info=reviewer_info,
                    review_lang=review_lang,
                    review_text=review_text,
                    review_date=review_date,
                    rating=rating,
                    number_of_photos=number_of_photos,
                ))
            break
        except Exception as e:
            print(f'Error scraping reviews: {e}. Retrying ({attempt+1}/{retries})...')
            if attempt < retries - 1:
                page.reload()
                page.wait_for_timeout(5000)
            else:
                print('Failed to scrape reviews after retries.')
                break
        
    print(f'Length of the review per restaurant: {len(reviews)}')  # instead of using length function in scrape restaurant data?, 
  
    return reviews, review_russian, review_other_l

# Function to scrape restaurant data from listings
def scrape_restaurant_data(page, listings, coordinate, unique_res_names):
    restaurant_list = RestaurantList()
    for listing in listings:
        try:
            listing.click()
            page.wait_for_timeout(random.randint(2000,5000)) #Decrease later 

            name_element = page.locator('//h1[contains(@class, "DUwDvf")]')
            price_element = page.locator('//span[contains(@class, "mgr77e")]//span//span').nth(3)
            type_element = page.locator('//button[contains(@class, "DkEaL ")]')
            address_element = page.locator('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]')
            website_element = page.locator('//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]')
            phone_number_element = page.locator('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]')
            review_count_element = page.locator('//div[@jsaction="pane.reviewChart.moreReviews"]//span')
            reviews_average_element = page.locator('//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]')

            #check if the restaurant name is already scraped
            restaurant_name = name_element.text_content() if name_element.count() > 0 else "N/A"
            if restaurant_name in unique_res_names:
                #skip to next 
                print(f"Skipping existing restaurant: {restaurant.name}")
                continue


            restaurant = Restaurant()
            # Name
            restaurant.name = name_element.text_content() if name_element.count() > 0 else "N/A"

            #Restaurant category
            restaurant.category = type_element.text_content() if type_element.count() > 0 else "N/A"
            
            #Restaurant Price Range
            price_string = price_element.text_content(timeout=3000) if type_element.count() > 0 else '0'
            range_ids = {"0": 0,"1–50": 1,"50–100": 2,"100–150": 3,"150–200": 4,"200–500": 5,"500+": 6}
            print(price_string)

            # 0: No Price Range Listed 1:AED 1-50; 2: AED 50-100; 3: AED 100-150; 4: AED 150-200; 5:AED 200- 500; 6:AED 500+
            if price_string != '0':
                price_string = price_string[4::]
            
            price_range = range_ids[price_string]
            print("Keyword to dict", price_string)
            print("Input to class", price_range)

            restaurant.price = price_range

           
            # Address
            restaurant.address = address_element.text_content() if address_element.count() > 0 else "N/A"
            
            # Website
            restaurant.website = website_element.text_content() if website_element.count() > 0 else "N/A"
            
            # Phone Number
            restaurant.phone_number = phone_number_element.text_content() if phone_number_element.count() > 0 else "N/A"
            
            # Review count #becareful with reviews and review FIX LATER
            restaurant.reviews_count = review_count_element.text_content() if review_count_element.count() > 0 else "N/A"
            
            # Review average
            restaurant.reviews_average = reviews_average_element.text_content() if reviews_average_element.count() > 0 else "N/A"
            
            #Get the coordinates of the restaurant
            restaurant.latitude, restaurant.longitude = get_coordinates_from_url(page.url)
            
            #Add the Search Key Used (for data cleaning later)
            restaurant.s_key = coordinate
            
            # Scrape reviews
            restaurant.reviews, restaurant.review_russian, restaurant.review_other_l = scrape_reviews(page)
            
            #number of scrapped reviews to compare with the all available reviews
            restaurant.scraped_review_count = len(restaurant.reviews) 
            
            #Add to the restaurant list
            restaurant_list.restaurant_list.append(restaurant)

        except Exception as e:
            print(f'Error: {e}')
    return restaurant_list

def visit_google_maps(page, url, retries=3):
    for attempt in range(retries):
        try:
            page.goto(url, timeout=60000)
            if "captcha" in page.url:
                print("CAPTCHA detected! Pausing scraping...")
                time.sleep(60)  # Wait and retry
                continue
            return True  # Successfully loaded page
        except Exception as e:
            print(f"Error visiting {url}: {e}. Retrying ({attempt+1}/{retries})...")
            time.sleep(random.uniform(5, 10))
    return False  # Failed after retries


# Main function to handle argument parsing and orchestrate scraping
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type = str)
    parser.add_argument("-t", "--total", type = int)
    args = parser.parse_args()

    search_for = "restaurant" 
    total = args.total if args.total else 1_000_000
    
    #Get coordinates from a file
    coordinates_file_path = os.path.join(os.getcwd(), 'coordinates.txt')
    if os.path.exists(coordinates_file_path):
        with open(coordinates_file_path, 'r') as file:
            #read line by line
            coordinates = [line.strip() for line in file.readlines()]
            print(coordinates)
    else:
        print('coordinates.txt file not found')
        sys.exit()
    
    #set to prevent duplicate data scraping
    unique_res_names = set()

    with sync_playwright() as p:
        
        for coordinate in coordinates:
            browser = p.chromium.launch(headless = False) #Change to True if everything is good
            page = browser.new_page()
            try:
                if not visit_google_maps(page,'https://www.google.com/maps/'+ coordinate):
                    print(f'Failed to visit coordinate {coordinate} after retries.')
                    continue

                #page.goto('https://www.google.com/maps/'+ coordinate, wait_until='load') 
                page.wait_for_timeout(5000) #sleep for 5 seconds to change

                page.locator('//input[@id="searchboxinput"]').fill(search_for)
                page.keyboard.press("Enter")
                page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

                listings = scrape_listings(page, total)
                restaurant_list = scrape_restaurant_data(page, listings, coordinate, unique_res_names)

                #restaurant_list.save_to_excel("google_maps_data_restaurant")
                restaurant_list.save_to_csv(coordinate)
                
                browser.close()
            except Exception as e:
                print(f'Error navigating to coordinate {coordinate}: {e}')
                browser.close()
                browser = p.chromium.launch(headless = False)
                page = browser.new_page()

        

if __name__ == "__main__":
    main()
