from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

from datetime import datetime
from argparse import ArgumentParser
from tqdm import tqdm
import time
import re

from utils import *

def find_open_schedules(driver):
    open_schedules = []
    try:
        # Find all events with "Open Times"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "appointments__date-cal-container"))
        )
        events = driver.find_elements(By.XPATH, "//div[contains(@class, 'rbc-event') and .//span[@class='rbc-event-available' and text()='Open Times']]")
        # print(f"Found {len(events)} open schedule(s)")

        for event in events:
            # Extract date from rbc-event-day-num or rbc-event-day-num--mobile
            try:
                date = event.find_element(By.CLASS_NAME, "rbc-event-day-num").text
            except NoSuchElementException:
                date = event.find_element(By.CLASS_NAME, "rbc-event-day-num--mobile").text
            open_schedules.append(int(date))
            # print(f"Open schedule on: {date}")
            # Optional: Click the event if needed
            # event.click()
    except TimeoutException:
        print("No open schedules found in this context")
    return open_schedules


def main(args):
    chrome_options = Options()

    if args.headless:
        chrome_options.add_argument("--headless=new") # for Chrome >= 109
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://www.dmv.ca.gov/portal/appointments/select-appointment-type?option=CID")

    found_schedules = []
    found_locations = []
    found_distances = []
    letters = driver.find_elements(By.CLASS_NAME, "page-numbers")
    j = 1
    with tqdm(total=24) as pbar:
        while j<25:
            time.sleep(2)
            i = 0
            locations = driver.find_elements(By.CLASS_NAME, "location-results__list-item")
            while (i<len(locations)):
                letters = driver.find_elements(By.CLASS_NAME, "page-numbers")
                l = letters[j]
                l.click()
                time.sleep(2)
                locations = driver.find_elements(By.CLASS_NAME, "location-results__list-item")
                loc = locations[i]
                location_name = loc.text.split('.')[1].split('\n')[0]
                location_postal_code = int(re.search(r"CA(.*?)\n", loc.text).group(1))
                select_location_button = loc.find_element(By.CLASS_NAME, "btn--select-loc")
                select_location_button.click()
                time.sleep(1)
                today_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Today']"))
                )
                time.sleep(1)
                today_button.click()
                schedules = [datetime(year=datetime.now().year, month=datetime.now().month, day=day) for day in find_open_schedules(driver)]
                distance = distance_between_zips(location_postal_code, args.zipcode)
                if distance < args.max_distance and len(schedules) > 0:
                    found_schedules.append(schedules)
                    found_locations.append(location_name)
                    found_distances.append(distance)

                return_button = driver.find_elements(By.CLASS_NAME, "appointment__panel-btn")[1]
                return_button.click()
                time.sleep(3)
                # print(len(locations))
                # print(locations[i].text)
                i+=1
            j+=1
        pbar.update(1)
        
    send_dmv_summary_email(args.recipient, found_locations, found_schedules, found_distances)



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--recipient', required=True)
    parser.add_argument('--max-distance', type=int, required=False, default=200)
    parser.add_argument('--zipcode', type=int, required=False, default=95301)
    parser.add_argument('--send-if-empty', action="store_true", default=False)
    parser.add_argument('--headless', action="store_true", default=False)
    args = parser.parse_args()
    main(args)