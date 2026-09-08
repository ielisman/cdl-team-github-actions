import random
import time
import traceback
import json
import os
import socket

from datetime                           import datetime
from dateutil.relativedelta             import relativedelta
from hashdiff                           import HashComparator
from notification_manager               import NotificationManager
from supabase_manager                   import SupabaseManager
from selenium                           import webdriver  
from selenium.common.exceptions         import WebDriverException, NoSuchElementException, TimeoutException, StaleElementReferenceException  # pyright: ignore[reportMissingImports]
from selenium.webdriver.chrome.service  import Service 
from selenium.webdriver.common.by       import By  
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select 
from webdriver_manager.chrome           import ChromeDriverManager  

from selenium_recaptcha_solver          import RecaptchaSolver 

# 1. https://www.python.org/downloads (Check the box "Add Python to PATH" or do it manually. python --version)
# 2. https://ffmpeg.org/download.html (download and extract to a folder, add the folder to PATH. ffmpeg -version)
# 3. pip install selenium webdriver-manager selenium-recaptcha-solver speechrecognition ffmpeg firebase-admin python-dateutil (pip show selenium ffmpeg ...)
#    optional: python -m pip install --upgrade pip

global_time_slots_per_location_date = {}
local_time_slots_per_location_date = {}
notification_manager = None
notifications_enabled = False
supabase_mgr = None
email_notifications_enabled = False
email_sender = ""
email_password = ""
email_recipients = []
consecutive_session_errors = 0


def load_config(config_path="rt_scanner_config.json"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resolved_path = os.path.join(script_dir, config_path)
    with open(resolved_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    required_root_keys = ["login", "student", "locations"]
    for key in required_root_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    if not config["locations"]:
        raise ValueError("Config key 'locations' must contain at least one location")

    return config


def get_config_or_env(config_value, env_var, placeholders=None):
    """Return config value unless it is blank/placeholder, then fall back to env var."""
    placeholders = placeholders or set()
    if config_value is None:
        return os.getenv(env_var, "")
    if isinstance(config_value, str):
        value = config_value.strip()
        if not value or value in placeholders:
            return os.getenv(env_var, "")
        return value
    return config_value

def setup_driver_original():
    chrome_options = webdriver.ChromeOptions()

    # user_profile = os.environ.get("USERPROFILE") # for Buster Chrome Extension but shadow elements doesn't work
    # buster_extension_path = os.path.join(user_profile,"AppData","Local","Google","Chrome","User Data","Profile 4","Extensions","mpbjkejclgfgadiemmefgebjfooflfhl", "3.1.0_0")
    # chrome_options.add_argument(f"--load-extension={buster_extension_path}")

    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-usb-discovery')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Prevent detection as automation
    chrome_options.add_argument('--disable-dev-shm-usage')  # Prevent shared memory issues
    chrome_options.add_argument('--no-sandbox')  # Disable sandboxing (useful in some environments)
    chrome_options.add_argument('--disable-extensions')  # Disable all Chrome extensions
    chrome_options.add_argument('--disable-notifications') 

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver    

def setup_driver():
    chrome_options = webdriver.ChromeOptions()

    # user_profile = os.environ.get("USERPROFILE") # for Buster Chrome Extension but shadow elements doesn't work
    # buster_extension_path = os.path.join(user_profile,"AppData","Local","Google","Chrome","User Data","Profile 4","Extensions","mpbjkejclgfgadiemmefgebjfooflfhl", "3.1.0_0")
    # chrome_options.add_argument(f"--load-extension={buster_extension_path}")

    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-usb-discovery')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Prevent detection as automation
    chrome_options.add_argument('--disable-dev-shm-usage')  # Prevent shared memory issues
    chrome_options.add_argument('--no-sandbox')  # Disable sandboxing (useful in some environments)
    chrome_options.add_argument('--disable-extensions')  # Disable all Chrome extensions
    chrome_options.add_argument('--disable-notifications') 

    # Additional noise-reduction flags; existing options above are intentionally unchanged.
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--metrics-recording-only')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--no-first-run')

    chrome_options.add_experimental_option(
        'prefs',
        {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
        },
    )
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(ChromeDriverManager().install(), log_output=os.devnull)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver, url, username, password):
    driver.get(url)
    driver.find_element(by=By.ID, value="UserName").clear()
    driver.find_element(by=By.ID, value="Password").clear()
    driver.find_element(by=By.ID, value="UserName").send_keys(username)
    driver.find_element(by=By.ID, value="Password").send_keys(password)
    driver.find_element(by=By.ID, value="Login1_btnPreLoginButton").click()

    try:
        login_continue_message = driver.find_element(by=By.ID, value="continueMessage")
        if login_continue_message.text == "If you continue, their session will be lost. Would you like to continue?":
            print(f"Found loginContinueMessage {login_continue_message.text}")
            driver.find_element(by=By.ID, value="confirmDialog").click()
            print("Found existing session. Cancelling it")
    except NoSuchElementException:
        print("No session to cancel. Continuing")

def navigate_to_booking_page(driver, url):
    print ("Navigating to booking page")
    driver.get(url)
    try:        
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, ".//iframe[@title='reCAPTCHA']"))
        )
        print("Found reCAPTCHA frame")
    except Exception as e:
        try:
            print("Did not find repCAPTCHA frame. Clicking on 'Scheduling' link")
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.ID, "hl_customMenu2269")))
            driver.find_element(by=By.ID, value="hl_customMenu2269").click()
            print("Clicked on 'Scheduling' link")
        except TimeoutException:
            print("Timeout: Element 'hl_customMenu2269' not found after waiting.")
        except Exception as e:
            print(f"navigate_to_booking_page Exception occurred: {e}")
            exit(1)

def solve_recaptcha(driver):
    try:
        solver = RecaptchaSolver(driver=driver)
        recaptcha_iframe = driver.find_element(By.XPATH, './/iframe[@title="reCAPTCHA"]')
        solver.click_recaptcha_v2(iframe=recaptcha_iframe)        
    except Exception as e:
        print(f"solve_recaptcha Exception occurred")
    finally:
        driver.switch_to.default_content()

def select_test_site(driver, site_name):    
    sites_select = Select(driver.find_element(by=By.ID, value="MainContent_ddlTestSiteId"))
    sites_select.select_by_visible_text(site_name)
    driver.find_element(By.ID, value="btnScheduleBookings").click()

def enter_cid_dob_cdlclass(driver, cid, dob, cdlclass):
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "txtCidDlgCid1"))
        )
        driver.find_element(By.ID, value="txtCidDlgCid1").clear()
        driver.find_element(By.ID, value="txtCidDlgCid1").send_keys(cid)
    except TimeoutException:
        print("Timeout: Element 'txtCidDlgCid1' not interactable after waiting.")
    except Exception as e:
        print(f"Exception occurred: {e}")
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "txtCidDlgDob1"))
        )
        driver.find_element(By.ID, value="txtCidDlgDob1").clear()
        driver.find_element(By.ID, value="txtCidDlgDob1").send_keys(dob)
    except TimeoutException:
        print("Timeout: Element 'txtCidDlgDob1' not interactable after waiting.")
    except Exception as e:
        print(f"Exception occurred: {e}")
    
    cdlClassSelect = Select(driver.find_element(by=By.ID, value="ddlCidDlgTestType1")) # Select CDL class
    cdlClassSelect.select_by_visible_text(cdlclass)    

def click_element_with_retry(driver, by, value, timeout_seconds=30, max_attempts=3):
    attempts = 0
    while attempts < max_attempts:
        try:
            element = WebDriverWait(driver, timeout_seconds).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except StaleElementReferenceException:
            print(f"StaleElementReferenceException clicking {value}. Retrying attempt {attempts + 1}")
        except TimeoutException:
            print(f"Timeout while waiting to click {value}. Attempt {attempts + 1}")
        except Exception as e:
            print(f"Exception clicking {value}: {e}. Attempt {attempts + 1}")
        attempts += 1
    return False

def check_eligibility(driver):

    # TODO: Please Verify if the following error occurs under class="error-message-label" (under parent div id="MainContent_vsClientInfoDlgErrMsg"):
    # There was a problem calling CheckElibility with client Id 910840069, test type A and retrieveImage False.
    # Retry N times or go back to Scheduling link

    if not click_element_with_retry(driver, By.ID, "chkClientInfoDlg", timeout_seconds=60, max_attempts=3):
        print("Failed to click chkClientInfoDlg after retries")
        
    if not click_element_with_retry(driver, By.ID, "btnClientInfoDlgCheckEligibility", timeout_seconds=30, max_attempts=3):
        print("Failed to click btnClientInfoDlgCheckEligibility after retries")
        return
    # here you can have the error: There was a problem calling CheckElibility with client Id

    okMsg  = driver.find_element(By.ID, value="MainContent_vsClientInfoDlgOkMsg")
    errMsg = driver.find_element(By.ID, value="MainContent_vsClientInfoDlgErrMsg")
    try:
        print ("Checking for All CIDs are eligible")
        WebDriverWait(driver, 90).until(
            EC.text_to_be_present_in_element((By.ID, "MainContent_vsClientInfoDlgOkMsg"), "All CIDs are eligible")
        )
        print ("Found text - All CIDs are eligible. Proceeding")
        if not click_element_with_retry(driver, By.ID, "btnClientInfoDlgContinue", timeout_seconds=30, max_attempts=3):
            print("Failed to click btnClientInfoDlgContinue after retries")
    except TimeoutException:
        print("Timeout: Element 'MainContent_vsClientInfoDlgOkMsg' cannot find such text.")
    except Exception as e:
        print(f"MainContent_vsClientInfoDlgOkMsg Exception occurred: {e}")

    if not click_element_with_retry(driver, By.ID, "chkClientInfoDlg", timeout_seconds=90, max_attempts=3):
        print("Unable to re-click chkClientInfoDlg after eligibility step")

def wait_for_calendar_page(driver):
    try:
        WebDriverWait(driver, 90).until(
            EC.text_to_be_present_in_element((By.ID, "MainContent_lblDetailsNote"), "Your account may hold up to")
        )
        print("Found text - Your account may hold up to ... Proceeding")
    except TimeoutException:
        print("Timeout: Element 'MainContent_lblDetailsNote' cannot find such text.")
    except Exception as e:
        print(f"MainContent_lblDetailsNote Exception occurred: {e}")   

def select_test_site_after_verification(driver, site_name):    
    sites_select = Select(driver.find_element(by=By.ID, value="MainContent_ddlDetailTestSiteId"))
    sites_select.select_by_visible_text(site_name)

def month_move(driver, direction, location=None, month_year=None):
    """
    Function to find the span under "div.navigator_transparent_titleright" or "div.navigator_transparent_titleleft",
    click on it, and retrieve the text under "div.navigator_transparent_title".
    If month_year is supplied, click until calendar_month_year equals month_year (maximum 3 clicks).
    """
    print(f"month_move: direction: {direction} location: {location} month_year: {month_year}")
    try:
        if month_year:
            # Loop up to 3 times to match the target month_year
            for attempt in range(3):
                # Locate the navigator_transparent_title element
                navigator_transparent_title = WebDriverWait(driver, 7).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.navigator_transparent_title"))
                )
                # Retrieve the text under the navigator_transparent_title element
                calendar_month_year = navigator_transparent_title.text
                print(f"Current calendar month and year: {calendar_month_year}. Location is {location}")

                # Check if the current calendar month and year matches the target month_year
                if calendar_month_year == month_year:
                    print(f"Target month and year '{month_year}' for location {location} was reached.")
                    return

                # Locate the direction div (e.g., titleright or titleleft)
                month_direction_div = driver.find_element(By.CSS_SELECTOR, direction)
                # Find the span inside the direction div and click on it
                month_direction_span = month_direction_div.find_element(By.TAG_NAME, "span")
                month_direction_span.click()
                print(f"Clicked inside {direction} ({location}). Attempt {attempt + 1}.")

            # If the loop completes and the target month_year is not reached
            print(f"Failed to reach target month and year '{month_year}' for {location} after 3 attempts.")
        else:
            # Original functionality: Click the specified direction once
            navigator_transparent_title = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.navigator_transparent_title"))
            )
            calendar_month_year = get_action(driver, navigator_transparent_title, By.CSS_SELECTOR, "div.navigator_transparent_title", lambda x: x.text.strip())
            # calendar_month_year = navigator_transparent_title.text
            # month_direction_div = driver.find_element(By.CSS_SELECTOR, direction)
            # month_direction_span = month_direction_div.find_element(By.TAG_NAME, "span")
            month_direction_span = driver.find_element(By.CSS_SELECTOR, f"{direction} span")
            get_action(driver, month_direction_span, By.CSS_SELECTOR, f"{direction} span", lambda x: x.click())
            # month_direction_span.click()
            navigator_transparent_title = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.navigator_transparent_title"))
            )
            calendar_month_year = get_action(driver, navigator_transparent_title, By.CSS_SELECTOR, "div.navigator_transparent_title", lambda x: x.text.strip())
            print(f"month_move: Clicked inside {direction} for location {location}. New calendar is {calendar_month_year}")
        time.sleep(random.uniform(1.135, 1.535))
    except TimeoutException:
        print(f"Timeout: {direction} for {location} was not found.")
    except Exception as e:
        print(f"Exception occurred while clicking inside {direction} {location}")

def process_div_busy_elements(driver, location):
        print(f"process_div_busy_elements: location: {location}")

        matrix =   [5,11,17,23,29,35,41,
                    6,12,18,24,30,36,42,
                    7,13,19,25,31,37,43,
                    8,14,20,26,32,38,44,
                    9,15,21,27,33,39,45]

        for index, el in enumerate(matrix):

                div_xpath = f"//*[@id='MainContent_dpDetailsNavigator']/div/div[{el}]"
                child_div_xpath = f"{div_xpath}//div[contains(@class, 'navigator_transparent_cell_text')]"

                div = driver.find_element(By.XPATH, div_xpath)
                class_attributes = get_action(driver, div, By.XPATH, div_xpath, lambda x: x.get_attribute("class").split())

                child_div = driver.find_element(By.XPATH, child_div_xpath)
                number = get_action(driver, div, By.XPATH, child_div_xpath, lambda x: x.text.strip())

                isGreenDate = False; isPreviousMonthDate = False; isNextMonthDate = False; isSelectedDate = False

                if "navigator_transparent_busy" in class_attributes:
                    if "navigator_transparent_dayother" in class_attributes and "navigator_transparent_day" not in class_attributes:
                        if index < 7:
                            isPreviousMonthDate = True
                        else:
                            isNextMonthDate = True

                    monyear_selector = "div.navigator_transparent_title"
                    monyear_title = driver.find_element(By.CSS_SELECTOR, monyear_selector)
                    calendar_month_year = get_action(driver, monyear_title, By.CSS_SELECTOR, monyear_selector, lambda x: x.text.strip())
                    date_obj = datetime.strptime(calendar_month_year, "%B %Y")

                    to_print = f"{el} {calendar_month_year}"
                    if isPreviousMonthDate:
                        target_month_date = date_obj - relativedelta(months=1)
                        target_month_date_obj = target_month_date.replace(day=int(number))
                        clicked_date = target_month_date_obj.strftime("%m/%d/%Y")
                    elif isNextMonthDate:
                        target_month_date = date_obj + relativedelta(months=1)
                        target_month_date_obj = target_month_date.replace(day=int(number))
                        clicked_date = target_month_date_obj.strftime("%m/%d/%Y")
                    else:
                        target_month_date_obj = date_obj.replace(day=int(number))
                        clicked_date = target_month_date_obj.strftime("%m/%d/%Y")

                    if "navigator_transparent_select" in class_attributes:
                        isSelectedDate = True # i.e. the first date when there are time slots available
                         
                    print(f"div[{el}]: {calendar_month_year} {clicked_date}")

                    if isNextMonthDate:
                        print(f"Skipping next month date: {clicked_date} for {location}. Will process it in the next month. Noting it")
                    elif isPreviousMonthDate:
                        print(f"Skipping previous month date: {clicked_date} for {location}. Will process it in the previous month. Noting it")
                    else:
                        if not isSelectedDate:
                            get_action(driver, div, By.XPATH, div_xpath, lambda x: x.click())
                        
                        time.sleep(random.uniform(1.135, 1.535))
                        process_time_slots(driver, location, clicked_date, True)
                        time.sleep(random.uniform(1.135, 1.535))

def process_time_slots(driver, location, appointments_date, viaGreenDate=False):
    print(f"process_time_slots: Appointments date: {appointments_date}")
    global local_time_slots_per_location_date
    try:
        time_slots_elements = WebDriverWait(driver, 5).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "#MainContent_dlDetailsSlots .js-schedule-time-slot")
        )
        time_slots_elements = get_multiple(driver, time_slots_elements, By.CSS_SELECTOR, "#MainContent_dlDetailsSlots .js-schedule-time-slot")
        time_slots_list = [slot.text for slot in time_slots_elements]
        if location not in local_time_slots_per_location_date:
            local_time_slots_per_location_date[location] = {}
        local_time_slots_per_location_date[location][appointments_date] = time_slots_list
        print(f"\tTime Slots for {location} {appointments_date} : {time_slots_list}")
    except TimeoutException:
        print("Timeout: Element 'MainContent_dlDetailsSlots' or time slots not found. Green day with no slots")
        if location not in local_time_slots_per_location_date:
            local_time_slots_per_location_date[location] = {}
        local_time_slots_per_location_date[location][appointments_date] = ['No slots']
    except Exception as e:
        print(f"process_time_slots: Exception occurred while counting time slots: {e}")
        
def _apply_differences_to_supabase(supabase_mgr, differences):
    """
    Translate a HashComparator.diff() result into scan_results row updates.

    added_locations / added_dates / added_times -> open_slot per time slot
    (the 'No slots' sentinel value is routed to mark_no_slots instead).
    removed_locations / removed_dates -> close every open slot for that
    location/date. removed_times -> close_slot per time slot.
    """
    no_slots = SupabaseManager._NO_SLOTS_SENTINEL

    def open_slots(by_location_date):
        for location, dates in by_location_date.items():
            for date, slots in dates.items():
                for time_slot in slots:
                    if time_slot == no_slots:
                        supabase_mgr.mark_no_slots(location, date)
                    else:
                        supabase_mgr.open_slot(location, date, time_slot)
                        supabase_mgr.clear_no_slots(location, date)

    open_slots(differences.get("added_locations", {}))
    open_slots(differences.get("added_dates", {}))
    open_slots(differences.get("added_times", {}))

    for location, dates in differences.get("removed_times", {}).items():
        for date, slots in dates.items():
            for time_slot in slots:
                supabase_mgr.close_slot(location, date, time_slot)

    for location, dates in differences.get("removed_dates", {}).items():
        for date in dates:
            supabase_mgr.close_all_open_for_date(location, date)

    for location, dates in differences.get("removed_locations", {}).items():
        for date in dates:
            supabase_mgr.close_all_open_for_date(location, date)


def process_one_verification(driver, locations):
    """
        1. Get current Month and Year.
        2. Verify if time slots are available immediately and get the date for it.
        3. Process all time slots for that date. Check if any other dates available and process if they are
        4. Move to next month and repeat the process.
        5. Move to the current month and change location of the site.
        6. Repeat steps 2-5 until all available time slots are processed for that location.
        7. Repeat steps 1-6 for all locations indefinitely.
    """

    global global_time_slots_per_location_date
    global local_time_slots_per_location_date
    global consecutive_session_errors

    local_time_slots_per_location_date = {}  # Reset for a clean scan cycle

    current_month_year = datetime.now().strftime("%B %Y")
    for location in locations:
        print(f"---------- SELECTING TEST SITE: {location}")
        select_test_site_after_verification(driver, location)
        time.sleep(random.uniform(1.135, 1.535))
        print(f"---------- FINDING ALL AVAILABLE DATES FOR {location} FOR {current_month_year}")
        process_div_busy_elements(driver, location)
        print(f"---------- MOVING INTO NEXT MONTH: {location}")
        month_move(driver, "div.navigator_transparent_titleright", location)
        print(f"---------- FINDING ALL AVAILABLE DATES FOR {location} FOR NEXT MONTH")
        process_div_busy_elements(driver, location)
        print(f"---------- MOVING BACK IN {location} FOR ORIGINAL MONTH {current_month_year}")
        month_move(driver, "div.navigator_transparent_titleleft", location, current_month_year)

    comparator = HashComparator()
    differences = comparator.diff(global_time_slots_per_location_date, local_time_slots_per_location_date)
    print(differences)
    send_notification(differences)

    # Apply the diff directly to Supabase: opened/closed slot rows per (location, date, time_slot)
    if supabase_mgr:
        try:
            _apply_differences_to_supabase(supabase_mgr, differences)
        except Exception as e:
            print(f"Supabase write error: {e}")

    global_time_slots_per_location_date = local_time_slots_per_location_date
    consecutive_session_errors = 0  # Full cycle completed cleanly; reset the restart budget

def process_calendar(driver, firebase_cred_path, locations, poll_interval_seconds=10,
                     notifications_enabled_value=False,
                     supabase_url="", supabase_key="", supabase_schema="public",
                     email_notifications_enabled_value=False, email_from="",
                     email_app_password="", email_to=None):

    global notification_manager, notifications_enabled, supabase_mgr
    global email_notifications_enabled, email_sender, email_password, email_recipients
    global global_time_slots_per_location_date
    notifications_enabled = notifications_enabled_value
    email_notifications_enabled = email_notifications_enabled_value
    email_sender = email_from
    email_password = email_app_password
    email_recipients = email_to or []

    if email_notifications_enabled and not (email_sender and email_password and email_recipients):
        print("Email notifications enabled but email_from/email_app_password/email_to are incomplete; disabling")
        email_notifications_enabled = False

    if notifications_enabled or email_notifications_enabled:
        notification_manager = NotificationManager(firebase_cred_path if notifications_enabled else None)
    else:
        print("Notifications are disabled by configuration")

    # Connect to Supabase for commands (pause / remote locations) and result persistence
    if supabase_url and supabase_key:
        try:
            supabase_mgr = SupabaseManager(supabase_url, supabase_key, supabase_schema)
            print(f"Supabase: connected (schema={supabase_schema})")

            # Seed in-memory state from currently-open rows so slots that closed
            # while the scanner was offline are still detected as removed.
            try:
                global_time_slots_per_location_date = supabase_mgr.get_open_slots_by_location_date()
                print(f"Supabase: seeded in-memory state from {sum(len(d) for d in global_time_slots_per_location_date.values())} open date(s)")
            except Exception as e:
                print(f"Supabase: could not seed in-memory state from existing rows: {e}")
        except Exception as e:
            print(f"Supabase init failed: {e}. Continuing without Supabase.")
            supabase_mgr = None
    else:
        print("Supabase URL/key not configured. Running without remote control.")
        supabase_mgr = None

    current_locations = list(locations)

    while True:
        print("\n ------------- Processing scan cycle ... -----------------")

        # Check remote commands (pause / updated locations) from the PWA
        if supabase_mgr:
            try:
                supabase_mgr.send_heartbeat(os.getpid(), socket.gethostname())
            except Exception as e:
                print(f"Supabase heartbeat error: {e}")
            try:
                commands = supabase_mgr.get_commands()
                if commands.get("paused", False):
                    print("Scanner PAUSED by remote command. Waiting 5 s ...")
                    time.sleep(5)
                    continue
                remote_locs = commands.get("locations")
                if remote_locs:
                    current_locations = remote_locs
            except Exception as e:
                print(f"Supabase command check error: {e}")

        process_one_verification(driver, current_locations)
        print(f"Sleeping for {poll_interval_seconds} seconds before next scan cycle")
        time.sleep(poll_interval_seconds)

def get_action(driver, html_element, by_locator, locator_value, operation, max_attempts=3):
    
    attempts = 0
    while attempts < max_attempts:
        try:
            return operation(html_element)
        except StaleElementReferenceException:
            print(f"StaleElementReferenceException encountered. Retrying {locator_value} ... Attempt {attempts + 1}")
            html_element = driver.find_element(by_locator, locator_value)
        except Exception as e:
            print(f"An error occurred: {e}. Retrying {locator_value} ... Attempt {attempts + 1}")
            html_element = driver.find_element(by_locator, locator_value)
        attempts += 1

    return None

def get_multiple(driver, html_elements, by_locator, locator_value, max_attempts=3):
    
    attempts = 0
    while attempts < max_attempts:
        try:
            time.sleep(random.uniform(0.135, 0.535))
            html_elements = driver.find_elements(by_locator, locator_value)
        except StaleElementReferenceException:
            print(f"StaleElementReferenceException encountered. Retrying {locator_value} ... Attempt {attempts + 1}")
            html_elements = driver.find_elements(by_locator, locator_value)
        except Exception as e:
            print(f"An error occurred: {e}. Retrying {locator_value} ... Attempt {attempts + 1}")
            html_elements = driver.find_elements(by_locator, locator_value)
        attempts += 1

    return html_elements

def send_notification(differences):

    global notification_manager
    global notifications_enabled
    global email_notifications_enabled, email_sender, email_password, email_recipients

    if not notifications_enabled and not email_notifications_enabled:
        print("Notifications disabled; skipping notification send")
        return

    result = ""
    for key in differences:
        if key == 'added_locations':
            locations = differences[key]
            for location in locations:
                result += f"{location}\n"
                for date, times in locations[location].items():
                    result += f" {date} : {', '.join(times)}\n"
        elif key == 'added_dates':
            locations = differences[key]
            for location in locations:
                result += f"{location} (new dates)\n"
                for date, times in locations[location].items():
                    result += f" {date} : {', '.join(times)}\n"
        elif key == 'added_times':
            locations = differences[key]
            for location in locations:
                
                result += f"{location} (new times or no slots)\n"
                for date, times in locations[location].items():
                    result += f" {date} : {', '.join(times)}\n"

    if result:
        print(f"Sending notification: {result}")
        if notifications_enabled:
            # Prefer FCM tokens stored in Firestore; fall back to hardcoded default token
            tokens = None
            if supabase_mgr:
                try:
                    tokens = supabase_mgr.get_fcm_tokens() or None
                except Exception as e:
                    print(f"Could not fetch FCM tokens from Supabase: {e}")
            notification_manager.send_firebase_notification(result, tokens)
        if email_notifications_enabled:
            notification_manager.send_email(
                email_sender, email_password, email_recipients,
                "Road Test Alert", result,
            )
    else:
        print("No new time slots detected. No notification sent.")

def _send_failure_email(email_enabled, email_from, email_app_password, email_to,
                         restart_allowed_on_error, restart_pause_minutes, error):
    """Notify by email that the scanner exceeded its consecutive-restart budget."""
    if not (email_enabled and email_from and email_app_password and email_to):
        print("Email notifications not fully configured; skipping failure email")
        return
    try:
        subject = "CDL Road Test Scanner: repeated failures, script paused"
        body = (
            f"The scanner failed {restart_allowed_on_error} consecutive time(s) while trying to "
            f"log in / read the calendar and is now pausing for {restart_pause_minutes} minute(s) "
            f"before trying again.\n\n"
            f"Last error:\n{error}\n\n"
            f"{traceback.format_exc()}"
        )
        manager = NotificationManager()
        manager.send_email(email_from, email_app_password, email_to, subject, body)
    except Exception as e:
        print(f"Failed to send failure notification email: {e}")


def main():
    config = load_config()

    login_config             = config["login"]
    student_config           = config["student"]
    locations                = config["locations"]
    firebase_cred_path       = config.get("firebase_cred_path", "./firebase_service_account.json")
    poll_interval_seconds    = config.get("poll_interval_seconds", 10)
    notifications_enabled_value = config.get("notifications_enabled", False)
    restart_interval_seconds = config.get("restart_interval_seconds", 30)
    restart_allowed_on_error = config.get("restart_allowed_on_error", 0) or 0
    restart_pause_minutes    = config.get("restart_pause_minutes", 15)
    email_notifications_enabled_value = config.get("email_notifications_enabled", False)
    email_from               = config.get("email_from", "")
    email_app_password       = get_config_or_env(
        config.get("email_app_password", ""),
        "GMAIL_APP_PASSWORD",
    )
    email_to                 = config.get("email_to", [])
    supabase_url             = get_config_or_env(
        config.get("supabase_url", ""),
        "SUPABASE_URL",
    )
    supabase_key             = get_config_or_env(
        config.get("supabase_service_key", ""),
        "SUPABASE_SERVICE_ROLE_KEY",
        {"YOUR_SUPABASE_SERVICE_ROLE_KEY"},
    )
    supabase_schema          = get_config_or_env(
        config.get("supabase_schema", "public"),
        "SUPABASE_SCHEMA",
    )

    global consecutive_session_errors

    # Claim ownership of scanner_commands before doing anything else. If another
    # instance is already alive on this machine (recent pid + heartbeat), refuse
    # to start a second scanner against the same site/account.
    scanner_pid = os.getpid()
    scanner_hostname = socket.gethostname()
    if supabase_url and supabase_key:
        try:
            owner_mgr = SupabaseManager(supabase_url, supabase_key, supabase_schema)
            heartbeat_stale_after_seconds = 15 * 60
            claimed = owner_mgr.claim_ownership_or_none(scanner_pid, scanner_hostname, heartbeat_stale_after_seconds)
            if claimed is None:
                commands = owner_mgr.get_commands()
                print(
                    f"Another scanner instance appears to be running: "
                    f"pid={commands.get('scanner_pid')} host={commands.get('scanner_hostname')} "
                    f"last_heartbeat={commands.get('scanner_heartbeat_at')}. Refusing to start a second instance."
                )
                return
            if student_config:
                owner_mgr.initialize_commands_if_missing(locations, student_config)
            owner_mgr.sync_locations_from_config(locations)
        except Exception as e:
            print(f"Supabase ownership check failed: {e}. Continuing without ownership guarantee.")

    while True:  # Outer restart loop — reinitialises Chrome after any failure
        # Prefer the PWA-managed active student from Supabase; fall back to
        # rt_scanner_config.json's "student" when Supabase has none configured.
        active_student = student_config
        if supabase_url and supabase_key:
            try:
                remote_student = SupabaseManager(supabase_url, supabase_key, supabase_schema).get_active_student()
                if remote_student:
                    active_student = remote_student
            except Exception as e:
                print(f"Could not fetch active student from Supabase: {e}. Using config default.")

        driver = None
        try:
            driver = setup_driver()
            login(driver, login_config["url"], login_config["username"], login_config["password"])
            navigate_to_booking_page(driver, login_config["booking_url"])
            solve_recaptcha(driver)
            select_test_site(driver, locations[0])
            enter_cid_dob_cdlclass(driver, active_student["cid"], active_student["dob"], active_student["cdl_class"])
            check_eligibility(driver)
            wait_for_calendar_page(driver)
            process_calendar(driver, firebase_cred_path, locations, poll_interval_seconds,
                             notifications_enabled_value,
                             supabase_url, supabase_key, supabase_schema,
                             email_notifications_enabled_value, email_from,
                             email_app_password, email_to)
        except Exception as e:
            print(f"Exception in main loop: {e}")
            traceback.print_exc()

            if restart_allowed_on_error > 0:
                consecutive_session_errors += 1
                print(f"Consecutive session-restart attempt {consecutive_session_errors}/{restart_allowed_on_error}")

                if consecutive_session_errors > restart_allowed_on_error:
                    print(
                        f"Exceeded restart_allowed_on_error={restart_allowed_on_error} consecutive failures. "
                        f"Pausing for {restart_pause_minutes} minute(s) before trying again."
                    )
                    _send_failure_email(
                        email_notifications_enabled_value, email_from, email_app_password, email_to,
                        restart_allowed_on_error, restart_pause_minutes, e,
                    )
                    time.sleep(restart_pause_minutes * 60)
                    consecutive_session_errors = 0  # Fresh budget after the pause
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        print(f"Restarting Chrome in {restart_interval_seconds} seconds ...")
        time.sleep(restart_interval_seconds)

if __name__ == "__main__":
    main()



# Change between RT sites
# <select name="ctl00$MainContent$ddlDetailTestSiteId" onchange="javascript:setTimeout('__doPostBack(\'ctl00$MainContent$ddlDetailTestSiteId\',\'\')', 0)" id="MainContent_ddlDetailTestSiteId" class="width99pct">
# 				<option value="">SELECT...</option>
# 				<option value="3358">3rd Party Bronx CDL Training Center</option>
# 				<option value="3366">3rd Party First Student BKLN</option>
# 				<option value="3341">3rd Party Greece CSD CDL</option>
# 				<option value="3335">3rd Party Huntington Coach E. Northport CDL</option>
# 				<option value="3332">3rd Party Huntington Coach-Hempstead CDL</option>
# 				<option value="240">3rd Party Vehicle Driving Program Wyandanch</option>
# 				<option value="194">3rd Party We Transport CDL Elmont</option>
# 				<option value="3191">Aqueduct CDL</option>
# 				<option value="2945">Auburn CDL</option>
#               <option value="3164">Bellerose CDL</option>
# 				<option value="3004">Brewster CDL</option>
# 				<option value="5444">Bronx CDL 2- Alexander Ave</option>
# 				<option value="904">Catskill CDL</option>
# 				<option value="2704">Cobleskill CDL</option>
# 				<option value="3165">College point CDL</option>
# 				<option value="1220">Coopers Plains CDL</option>
# 				<option value="8">East Patchogue CDL</option>
# 				<option value="3185">Endicott CDL</option>
# 				<option selected="selected" value="2964">Fresh Kills CDL</option>
# 				<option value="3186">Geneva CDL</option>
# 				<option value="2185">Glen CDL</option>
# 				<option value="1904">Glens Falls CDL</option>
# 				<option value="3124">Goshen CDL</option>
# 				<option value="1405">IPARK84 CDL</option>
# 				<option value="2764">Jamestown CDL</option>
# 				<option value="872">Johnstown</option>
# 				<option value="2804">Kingston CDL</option>
# 				<option value="2805">Kingston CDL/NYS Thruway</option>
# 				<option value="2802">Kingston Plaza CDL</option>
# 				<option value="8485">Leroy CDL</option>
# 				<option value="8000000">Lowville CDL</option>
# 				<option value="2947">Massena CDL</option>
# 				<option value="2924">Monticello CDL</option>
# 				<option value="3194">Nassau CC CDL</option>
# 				<option value="1447">Newburgh CDL NYS Thruway Exit 17</option>
# 				<option value="2787">Ogdensburg CDL</option>
# 				<option value="99999999">Oneonta CDL</option>
# 				<option value="1964">Orangeburg CDL</option>
# 				<option value="3084">Oswego CDL</option>
# 				<option value="2864">Plattsburgh CDL</option>
# 				<option value="2021">Raceway CDL</option>
# 				<option value="878">Rochester CDL</option>
# 				<option value="2950">Sanborn CDL</option>
# 				<option value="8781">Schenectady Co Airport CDL</option>
# 				<option value="34">South Hicksville CDL</option>
# 				<option value="42">Syosset CDL</option>
# 				<option value="1124">Syracuse CDL</option>
# 				<option value="108">Tarrytown CDL</option>
# 				<option value="3189">Uniondale CDL</option>
# 				<option value="3024">Warsaw CDL</option>
# 				<option value="2946">Watertown CDL</option>
# 				<option value="2904">West Seneca CDL</option>
# 				<option value="2944">Westmoreland Thruway Tandem Lot CDL</option>
# 			</select>

# def solve_recaptcha_orig(driver):

#     ## use Buster Chrome Extension solver-button: 
#     # https://chromewebstore.google.com/detail/Buster:%20Captcha%20Solver%20for%20Humans/mpbjkejclgfgadiemmefgebjfooflfhl?hl=en
#     ## div.rc-imageselect-desc-wrapper if recaptcha checkbox appears
#     ## id="recaptcha-anchor", aria-checked="true"

#     try:
#         print("Finding reCAPTCHA frame")
#         WebDriverWait(driver, 100).until(
#             EC.presence_of_element_located((By.XPATH, ".//iframe[@title='reCAPTCHA']"))
#         )
#         driver.switch_to.frame(driver.find_element(By.XPATH, value=".//iframe[@title='reCAPTCHA']"))
#         print("Switched to reCAPTCHA frame")

#         print("recaptchaCheckBox - checking state if clicked")
#         recaptcha_checkbox = driver.find_element(by=By.ID, value="recaptcha-anchor")
#         recaptcha_checkbox.click()
            
#         WebDriverWait(driver, 90).until(
#             EC.text_to_be_present_in_element_attribute(
#                 (By.ID, "recaptcha-anchor"), "aria-checked", "true"
#             )
#         )
#         print("recaptchaCheckBox - checked")
#     except Exception as e:
#         print(f"Recaptcha is not checked. Exception occurred: {e}")
#         traceback.print_exc()
#         exit(1)
#     finally:
#         driver.switch_to.default_content()


# def process_div_busy_elements_new(driver, location):
#         try:
#             sorted_numbers = sorted(
#                 int(div.text.strip()) for div in driver.find_elements(By.XPATH, "//div[contains(@class, 'navigator_transparent_busy')]/div[contains(@class, 'navigator_transparent_cell_text')]")
#             )
#             print(f"Sorted numbers: {sorted_numbers}") # works good, issue is when numbers repeat

#             # TODO find the green date via navigator_transparent_busy and div element path for that date, 
#             # TODO i.e. //*[@id="MainContent_dpDetailsNavigator"]/div/div[27]/div[2] because date from previous month, i.e. Apr 1 can be together with May 1
#             # TODO or go over the dev components instead of dates, i.e. div[5], div[11], div[17], div[23], div[29], div[35], div[41], 
#             # TODO                                                      div[6], div[12], div[18], div[24], div[30], div[36], div[42],
#             # TODO                                                      div[7], div[13], div[19], div[25], div[31], div[37], div[43], 
#             # TODO                                                      div[8], div[14], div[20], div[26], div[32], div[38], div[44],
#             # TODO                                                      div[9], div[15], div[21], div[27], div[33], div[39], div[45]

#             exit(0)

#             matrix = [5,11,17,23,29,35,41,
#                       6,12,18,24,30,36,42,
#                       7,13,19,25,31,37,43,
#                       8,14,20,26,32,38,44,
#                       9,15,21,27,33,39,45]

#             # Iterate over each sorted number
#             for number in sorted_numbers:
#                 try:
#                     # Wait for the parent div of the number to be present and interactable
#                     # //*[@id="MainContent_dlDetailsSlots_lblDetailsTimeSlot_0"]
#                     # /html/body/div[1]/form[1]/div[5]/div[3]/div[3]/div/div/div[4]/table/tbody/tr/td[2]/fieldset/table/tbody/tr/td[1]/div/span
#                     parent_div = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((
#                             By.XPATH,
#                             f"//div[contains(@class, 'navigator_transparent_busy')]/div[contains(@class, 'navigator_transparent_cell_text') and text()='{number}']/.."
#                         ))
#                     )
#                     print(f"Clicking on parent div for number: {number}")
#                     parent_div.click()

#                     # Wait for staleness of the clicked element to ensure the page updates
#                     WebDriverWait(driver, 10).until(EC.staleness_of(parent_div))
#                     print(f"Successfully clicked on parent div for number: {number}")

#                     # Optional: Add a short delay to avoid overwhelming the server
#                     time.sleep(1)

#                 except TimeoutException:
#                     print(f"Timeout: Could not find or interact with the parent div for number {number}.")
#                 except Exception as e:
#                     print(f"Error while processing number {number}: {e}")
#                     continue

#         except ValueError:
#             print("Error: One of the elements contains non-numeric text.")
#         except Exception as e:
#             print(f"An unexpected error occurred: {e}")

# def process_time_slots_v1(driver, location, appointments_date, viaGreenDate=False):
#     print(f"process_time_slots: Appointments date: {appointments_date}")
#     global local_time_slots_per_location_date

#     try:
#         slots_table = WebDriverWait(driver, 5).until(
#             EC.presence_of_element_located((By.ID, "MainContent_dlDetailsSlots"))
#         )
#         # get_action(driver, slots_table, By.ID, "MainContent_dlDetailsSlots", lambda x: x.id)                
#         # Count the number of elements with the class "schedule-time-slot" under the table
#         time_slots_elements = []
#         time_slots_list = []
#         time_slots_elements = slots_table.find_elements(By.CLASS_NAME, "js-schedule-time-slot")            
#         for slot in time_slots_elements:
#             # print(f"{appointments_date} Time slot {index}: {slot.text}")
#             time_slots_list.append(slot.text)                        
#         # Hash time_slots_list against location and date
#         if location not in local_time_slots_per_location_date:
#             local_time_slots_per_location_date[location] = {}
#         local_time_slots_per_location_date[location][appointments_date] = time_slots_list
#         print(f"Time Slots for {location} {appointments_date} : {time_slots_list}")
#     except TimeoutException:
#         print("Timeout: Element 'MainContent_dlDetailsSlots' not found. Green day with no slots")
#     except Exception as e:
#         print(f"process_time_slots: Exception occurred while counting time slots") 

# def process_time_slots_orig(driver, location, appointments_date=None, viaGreenDate=False):
#     """
#     Function to process time slots under the element with id 'MainContent_dlDetailsSlots'.
#     """
#     global local_time_slots_per_location_date

#     if appointments_date is None:
#         # print("Appointments date text not provided. Using current date.")
#         appointments_date = datetime.now().strftime("%m/%d/%Y")

#     print(f"process_time_slots: Appointments date: {appointments_date}")
#     is_error_message = False
#     is_error_message_element = True
#     try:
#         error_message_label = WebDriverWait(driver, 2.3).until(
#             EC.presence_of_element_located((By.XPATH, "//*[@id='MainContent_pnlDetails']/div[4]/table/tbody/tr/td[2]/fieldset/div/span"))
#         )
#         # print(f"process_time_slots: Appointment text: {error_message_label.text}")
#         if "No appointments" in error_message_label.text:
#             print(f"No appointments found for {appointments_date}.")
#             is_error_message = True
#             if viaGreenDate:
#                 print(f"Found Green Date for {location} {appointments_date} with no time slots")
#                 if location not in local_time_slots_per_location_date:
#                     local_time_slots_per_location_date[location] = {}
#                 local_time_slots_per_location_date[location][appointments_date] = []                
#     except TimeoutException:
#         print("Timeout: Element 'error-message-label' not found.")
#         is_error_message_element = False # it should exists with empty text when there are time slots
#     except Exception as e:
#         print(f"process_time_slots: Exception occurred for 'error-message-label'")    

#     if not is_error_message and is_error_message_element:
#         try:
#             slots_table = WebDriverWait(driver, 5).until(
#                 EC.presence_of_element_located((By.ID, "MainContent_dlDetailsSlots"))
#             )                
#             # Count the number of elements with the class "schedule-time-slot" under the table
#             time_slots_elements = []
#             time_slots_list = []
#             time_slots_elements = slots_table.find_elements(By.CLASS_NAME, "js-schedule-time-slot")            
#             for index, slot in enumerate(time_slots_elements):
#                 # print(f"{appointments_date} Time slot {index}: {slot.text}")
#                 time_slots_list.append(slot.text)                        
#             # Hash time_slots_list against location and date
#             if location not in local_time_slots_per_location_date:
#                 local_time_slots_per_location_date[location] = {}
#             local_time_slots_per_location_date[location][appointments_date] = time_slots_list
#             print(f"Time Slots for {location} {appointments_date} : {time_slots_list}")
#         except TimeoutException:
#             print("Timeout: Element 'MainContent_dlDetailsSlots' not found.")
#         except Exception as e:
#             print(f"process_time_slots: Exception occurred while counting time slots")
