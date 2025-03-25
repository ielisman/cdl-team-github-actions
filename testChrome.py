import random
import time
import traceback

from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager


def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maximized')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def login(driver, username, password):
    driver.get("https://www.nyakts.com/Login.aspx?mid=2269")
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
        WebDriverWait(driver, 30).until(
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
            print(f"Exception occurred: {e}")
            exit(1)

def solve_recaptcha(driver):
    try:
        print("Finding reCAPTCHA frame")
        WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.XPATH, ".//iframe[@title='reCAPTCHA']"))
        )
        driver.switch_to.frame(driver.find_element(By.XPATH, value=".//iframe[@title='reCAPTCHA']"))
        print("Switched to reCAPTCHA frame")

        print("recaptchaCheckBox - checking state if clicked")
        recaptcha_checkbox = driver.find_element(by=By.ID, value="recaptcha-anchor")
        recaptcha_checkbox.click()
        WebDriverWait(driver, 90).until(
            EC.text_to_be_present_in_element_attribute(
                (By.ID, "recaptcha-anchor"), "aria-checked", "true"
            )
        )
        print("recaptchaCheckBox - checked")
    except Exception as e:
        print(f"Recaptcha is not checked. Exception occurred: {e}")
        traceback.print_exc()
        exit(1)
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

def check_eligibility(driver):
    try:        
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "chkClientInfoDlg")))        
        driver.find_element(By.ID, value="chkClientInfoDlg").click() 
    except TimeoutException:
        print("Timeout: Element 'chkClientInfoDlg' not interactable after waiting.")
    except Exception as e:
        print(f"chkClientInfoDlg Exception occurred: {e}")
    
    driver.find_element(By.ID, value="btnClientInfoDlgCheckEligibility").click()
    okMsg  = driver.find_element(By.ID, value="MainContent_vsClientInfoDlgOkMsg")
    errMsg = driver.find_element(By.ID, value="MainContent_vsClientInfoDlgErrMsg")
    try:
        print ("Checking for All CIDs are eligible")
        WebDriverWait(driver, 60).until(
            EC.text_to_be_present_in_element((By.ID, "MainContent_vsClientInfoDlgOkMsg"), "All CIDs are eligible")
        )
        print ("Found text - All CIDs are eligible. Proceeding")   
        driver.find_element(By.ID, value="btnClientInfoDlgContinue").click()
    except TimeoutException:
        print("Timeout: Element 'MainContent_vsClientInfoDlgOkMsg' cannot find such text.")
    except Exception as e:
        print(f"MainContent_vsClientInfoDlgOkMsg Exception occurred: {e}")

    try:        
        WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "chkClientInfoDlg")))        
        driver.find_element(By.ID, value="chkClientInfoDlg").click()
    except TimeoutException:
        print("Timeout: Element 'chkClientInfoDlg' not interactable after waiting.")
    except Exception as e:
        print(f"chkClientInfoDlg Exception occurred: {e}")

def wait_for_calendar_page(driver):
    try:
        WebDriverWait(driver, 60).until(
            EC.text_to_be_present_in_element((By.ID, "MainContent_lblDetailsNote"), "Your account may hold up to")
        )
        print("Found text - Your account may hold up to ... Proceeding")
    except TimeoutException:
        print("Timeout: Element 'MainContent_lblDetailsNote' cannot find such text.")
    except Exception as e:
        print(f"MainContent_lblDetailsNote Exception occurred: {e}")   

def process_calendar(driver):
    div_busy_elements = []
    while not div_busy_elements:
        div_busy_elements = driver.find_elements(By.CSS_SELECTOR, "div.navigator_transparent_busy")
        if not div_busy_elements:
            print("No div_busy elements found. Retrying...")
            time.sleep(random.randint(3, 15))

    print(f"Found {len(div_busy_elements)} div_busy elements.")
    div_with_numbers = []

    for index, div in enumerate(div_busy_elements):
        try:
            inner_div = div.find_element(By.XPATH, ".//div[contains(@class, 'navigator_transparent_cell_text')]")
            number = int(inner_div.text.strip())
            div_with_numbers.append((index, number))
        except Exception as e:
            print(f"Error while processing element: {e}")
            continue

    div_with_numbers.sort(key=lambda x: x[1])

    for index, number in div_with_numbers:
        try:
            div_busy_elements = driver.find_elements(By.CSS_SELECTOR, "div.navigator_transparent_busy")
            try:
                div = div_busy_elements[index]
            except IndexError:
                print(f"IndexError: div_busy_elements list has changed. Skipping index {index}.")
                continue

            print(f"Number found: {number}")
            div.click()
            print(f"Clicked on {number}")
            time.sleep(random.randint(1, 3))
        except Exception as e:
            print(f"Error while processing element: {e}")
            continue              

def main():
    driver = setup_driver()
    try:
        login(driver, "7583ds", "Ditmas_201!")
        navigate_to_booking_page(driver, "https://www.nyakts.com/NyRstApps/ThirdPartyBooking.aspx?mid=2269")
        solve_recaptcha(driver)
        select_test_site(driver, "Fresh Kills CDL")
        enter_cid_dob_cdlclass(driver, "910840069", "06/29/1988", "CDL A (Class A CDL)")
        check_eligibility(driver)
        wait_for_calendar_page(driver)
        process_calendar(driver)
    except Exception as e:
        print(f"Exception occurred: {e}")
    finally:
        time.sleep(300)
        driver.quit()

if __name__ == "__main__":
    main()

# <span class="recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox
#            aria-checked="false"
# <span class="recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox recaptcha-checkbox-checked"
#            aria-checked="true"
#            aria-disabled="false"
#            style="overflow: visible;"

# HTML structure for reCAPTCHA checkbox
# <div class="rc-inline-block">
#  <div class="rc-anchor-center-container">
#   <div class="rc-anchor-center-item rc-anchor-checkbox-holder">
#    <span class="recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox"
#            role="checkbox"
#            aria-checked="false"
#            id="recaptcha-anchor"
#            tabindex="0"
#            dir="ltr"
#            aria-labelledby="recaptcha-anchor-label">
#               <div class="recaptcha-checkbox-border" role="presentation"></div>
#               <div class="recaptcha-checkbox-borderAnimation" role="presentation"></div>
#               <div class="recaptcha-checkbox-spinner" role="presentation">
#                  <div class="recaptcha-checkbox-spinner-overlay"></div>
#               </div>
#               <div class="recaptcha-checkbox-checkmark" role="presentation"></div>
#    </span>
#   </div>
#  </div>
# </div>

# <div class="rc-inline-block">
#  <div class="rc-anchor-center-container">
#   <div class="rc-anchor-center-item rc-anchor-checkbox-holder">
#    <span class="recaptcha-checkbox goog-inline-block recaptcha-checkbox-unchecked rc-anchor-checkbox recaptcha-checkbox-checked"
#           role="checkbox"
#           aria-checked="true"
#           id="recaptcha-anchor"
#           dir="ltr"
#           aria-labelledby="recaptcha-anchor-label"
#           aria-disabled="false"
#           tabindex="0"
#           style="overflow: visible;">
#             <div class="recaptcha-checkbox-border" role="presentation" style="display: none;"></div>
#             <div class="recaptcha-checkbox-borderAnimation" role="presentation" style=""></div>
#             <div class="recaptcha-checkbox-spinner" role="presentation" style="display: none; animation-play-state: running; opacity: 1;">
#               <div class="recaptcha-checkbox-spinner-overlay" style="animation-play-state: running;"></div>
#             </div>
#             <div class="recaptcha-checkbox-checkmark" role="presentation" style=""></div>
#    </span>
#   </div>
#  </div>
# </div>

# ----------------- arrow back
# <div unselectable="on" class="navigator_transparent_titleleft" style="position: absolute; left: 0px; top: 0px; width: 20px; height: 20px; line-height: 20px; cursor: pointer;"><span>&lt;</span></div>

# ----------------- arrow front
# <div unselectable="on" class="navigator_transparent_titleright" style="position: absolute; left: 120px; top: 0px; width: 20px; height: 20px; line-height: 20px; cursor: pointer;"><span>&gt;</span></div>

# ----------------- Today's date
# <div class="navigator_transparent_day navigator_transparent_cell navigator_transparent_today navigator_transparent_dayother navigator_transparent_select" unselectable="on" style="position: absolute; left: 60px; top: 100px; width: 20px; height: 20px; line-height: 20px; cursor: pointer;"><div class="navigator_transparent_todaybox navigator_transparent_cell_box" style="position: absolute; inset: 0px;"></div><div class="navigator_transparent_cell_text" style="position: absolute; inset: 0px;">20</div></div>

# ----------------- First available non-green date
# <div class="navigator_transparent_day      navigator_transparent_cell"                            unselectable="on" style="position: absolute; left: 20px; top: 120px; width: 20px; height: 20px; line-height: 20px; cursor: pointer;"><div class="navigator_transparent_daybox navigator_transparent_cell_box" style="position: absolute; inset: 0px;"></div><div class="navigator_transparent_cell_text" style="position: absolute; inset: 0px;">25</div></div>

# ----------------- First available green date
# <div class="navigator_transparent_day      navigator_transparent_cell navigator_transparent_busy" unselectable="on" style="position: absolute; left: 0px;  top: 140px; width: 20px; height: 20px; line-height: 20px; cursor: pointer;"><div class="navigator_transparent_daybox navigator_transparent_cell_box" style="position: absolute; inset: 0px;"></div><div class="navigator_transparent_cell_text" style="position: absolute; inset: 0px;">31</div></div>

# ----------------- First available green date with time slots (dayother means other month if we are in prev month)
# <div class="navigator_transparent_dayother navigator_transparent_cell navigator_transparent_busy" unselectable="on" style="position: absolute; left: 80px; top: 140px; width: 20px; height: 20px; line-height: 20px; cursor: pointer;"><div class="navigator_transparent_daybox navigator_transparent_cell_box" style="position: absolute; inset: 0px;"></div><div class="navigator_transparent_cell_text" style="position: absolute; inset: 0px;">4</div></div>

# ----------------- Date of time slots
# <legend class="fwd">Available Appointments: <span id="MainContent_lblDeailsBookDate">04/04/2025</span></legend>

# ----------------- Table of time slots
# <table id="MainContent_dlDetailsSlots" class="datalist-item" cellspacing="0" style="border-collapse:collapse;">
# 				<tbody><tr>
# 					<td>
#                                                 <div class="schedule-time-slot">
#                                                     <span id="MainContent_dlDetailsSlots_lblDetailsTimeSlot_0" class="js-schedule-time-slot" data-slotid="3046034">12:45 PM </span>
#                                                 </div>
#                                             </td><td>
#                                                 <div class="schedule-time-slot">
#                                                     <span id="MainContent_dlDetailsSlots_lblDetailsTimeSlot_1" class="js-schedule-time-slot" data-slotid="3046033">02:00 PM (2.00)</span>
#                                                 </div>
#                                             </td><td></td><td></td><td></td><td></td><td></td><td></td>
# 				</tr>
# 			</tbody></table>

# ----------------- Showing message that No appointments are available (parent: <fieldset class="size99pct">)
# <div class="error-message ">
#  <span class="error-message-label">No appointments for test type CDL A are available for the selected date.</span>
# </div>

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
