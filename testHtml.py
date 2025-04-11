import os
import random
import time
import traceback

from datetime                           import datetime
from dateutil.relativedelta             import relativedelta
from hashdiff                           import HashComparator
from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

from selenium_recaptcha_solver          import RecaptchaSolver


# 1. https://www.python.org/downloads (Check the box "Add Python to PATH" or do it manually. python --version)
# 2. https://ffmpeg.org/download.html (download and extract to a folder, add the folder to PATH. ffmpeg -version)
# 3. pip install selenium webdriver-manager selenium-recaptcha-solver speechrecognition ffmpeg firebase-admin (pip show selenium ffmpeg ...)
#    optional: python -m pip install --upgrade pip

global_time_slots_per_location_date = {}
local_time_slots_per_location_date = {}
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def process_div_busy_elements_new(driver, location):
        
        matrix =   [5,11,17,23,29,35,41,
                    6,12,18,24,30,36,42,
                    7,13,19,25,31,37,43,
                    8,14,20,26,32,38,44,
                    9,15,21,27,33,39,45]

        for index, el in enumerate(matrix): 
            try:

                div_xpath = f"//*[@id='MainContent_dpDetailsNavigator']/div/div[{el}]"
                child_div_xpath = f"{div_xpath}//div[contains(@class, 'navigator_transparent_cell_text')]"
                
                print(f"\tprocess_div_busy_elements div_xpath {el}")
                div = driver.find_element(By.XPATH, div_xpath)
                class_attributes = get_action(driver, div, By.XPATH, div_xpath, lambda x: x.get_attribute("class").split())
                #class_attributes = div.get_attribute("class").split()

                print(f"\tprocess_div_busy_elements child_div_xpath {el}")
                child_div = driver.find_element(By.XPATH, child_div_xpath)
                number = get_action(driver, div, By.XPATH, child_div_xpath, lambda x: x.text.strip())
                # number = child_div.text.strip()

                isGreenDate = False; isPreviousMonthDate = False; isNextMonthDate = False

                if "navigator_transparent_busy" in class_attributes:
                    if "navigator_transparent_dayother" in class_attributes and "navigator_transparent_day" not in class_attributes:
                        if index < 7:
                            isPreviousMonthDate = True
                        else:
                            isNextMonthDate = True

                    navigator_transparent_title = WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.navigator_transparent_title")))
                    calendar_month_year = navigator_transparent_title.text.strip()
                    date_obj = datetime.strptime(f"{calendar_month_year}", "%B %Y")

                    to_print = f"DIV[{el}] DN={number} my={calendar_month_year} attr={class_attributes}"
                    if isPreviousMonthDate:
                        target_month_date = date_obj - relativedelta(months=1)
                        target_month_date_obj = target_month_date.replace(day=int(number))
                        clicked_date = target_month_date_obj.strftime("%m/%d/%Y")
                        to_print = f"{to_print} => previous month date {clicked_date}"
                    elif isNextMonthDate:
                        target_month_date = date_obj + relativedelta(months=1)
                        target_month_date_obj = target_month_date.replace(day=int(number))
                        clicked_date = target_month_date_obj.strftime("%m/%d/%Y")
                        to_print = f"{to_print} => next month date {clicked_date}"
                    else:
                        target_month_date_obj = date_obj.replace(day=int(number))
                        clicked_date = target_month_date_obj.strftime("%m/%d/%Y")
                        to_print = f"{to_print} => current month date {clicked_date}"

                    if "navigator_transparent_select" in class_attributes:
                        to_print = f"{to_print} => sel date" # i.e. the first date when there are time slots available

                    print(to_print)
                    get_action(driver, div, By.XPATH, div_xpath, lambda x: x.click())
                    sleep_time = random.uniform(0.75, 1.135)

                    process_time_slots(driver, "Nassau CC CDL", clicked_date, True) # already processed once   

            except Exception as e:
                print(f" => Exception occurred: {e}")

from selenium.common.exceptions import StaleElementReferenceException

def get_action(driver, html_element, by_locator, locator_value, operation, max_attempts=3):
    
    attempts = 0
    while attempts < max_attempts:
        try:
            return operation(html_element)
        except StaleElementReferenceException:
            print(f"StaleElementReferenceException encountered. Retrying... Attempt {attempts + 1}")
            html_element = driver.find_element(by_locator, locator_value)
        except Exception as e:
            print(f"An error occurred: {e}")
            html_element = driver.find_element(by_locator, locator_value)
        attempts += 1

    return result

def process_time_slots(driver, location, appointments_date=None, viaGreenDate=False):
    print (f"Processing time slots for {location} on {appointments_date}")

def main():
    driver = setup_driver()
    try:
        # Get the absolute path of test.html
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_html_path = os.path.join(current_dir, "test.html")
        test_html_url = f"file://{test_html_path}"  # Add the file:// prefix

        # Open the test.html file
        driver.get(test_html_url)
        process_div_busy_elements_new(driver, "Nassau CC CDL")
    except Exception as e:
        print(f"Exception occurred: {e}")
    finally:
        time.sleep(30000)
        driver.quit()

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

