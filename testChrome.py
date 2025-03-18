import time
import traceback

from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

try:
    # LOGIN
    driver.get("https://www.nyakts.com/Login.aspx?mid=2269") # Navigate to login page
    # driver.get("https://www.nyakts.com/NyRstApps/ThirdPartyBooking.aspx?mid=2269")    
    driver.find_element(by=By.ID, value="UserName").clear() # Clear username field
    driver.find_element(by=By.ID, value="Password").clear() # Clear password field
    driver.find_element(by=By.ID, value="UserName").send_keys("7583ds") # Enter username
    driver.find_element(by=By.ID, value="Password").send_keys("Ditmas_201!") # Enter password
    driver.find_element(by=By.ID, value="Login1_btnPreLoginButton").click() # Click login button

    cancelOtherSession = False
    try:
        loginContinueMessage = driver.find_element(by=By.ID, value="continueMessage") # Check for existing session message
        if loginContinueMessage.text == "If you continue, their session will be lost. Would you like to continue?":
            print(f"Found loginContinueMessage {loginContinueMessage.text}")
        driver.find_element(by=By.ID, value="confirmDialog").click() # Confirm to cancel other session
        print(f"Found existing session. Cancelling it")
        cancelOtherSession = True
    except Exception as es:
        print(f"No session to cancel. Continuing")

    driver.get("https://www.nyakts.com/NyRstApps/ThirdPartyBooking.aspx?mid=2269") # Navigate to booking page    

    # driver.switch_to.default_content()
    try:  
        print("Finding reCAPTCHA frame")
        WebDriverWait(driver, 100).until(
            EC.presence_of_element_located(
                (By.XPATH, ".//iframe[@title='reCAPTCHA']")
            )
        )
        driver.switch_to.frame(driver.find_element(By.XPATH, value=".//iframe[@title='reCAPTCHA']")) # Switch to reCAPTCHA frame
        print("Switched to reCAPTCHA frame")
    except Exception as e:
        print(f"Exception while switching to reCAPTCHA frame: {e}")
    
    # recaptcha-checkbox-checkmark
    try:  
        print("recaptchaCheckBox - checking state if clicked")              
        recaptchaCheckBox = driver.find_element(by=By.ID, value="recaptcha-anchor")
        recaptchaCheckBox.click()
        WebDriverWait(driver, 90).until(
            EC.text_to_be_present_in_element_attribute(
                (By.ID, "recaptcha-anchor"),
                "aria-checked",
                "true")
        ) # Wait until reCAPTCHA is checked
        print("recaptchaCheckBox - checked")         
    except Exception as e:
        print(f"Recaptcha is not checked. Exception occured", e)
        traceback.print_exc()
        exit(1)

    driver.switch_to.default_content()

    # Here we can interfere by hand in case captcha appears
    # We will check for the element of captcha. If exists, we will explicitly wait until it is solved
    sitesSelect = Select(driver.find_element(by=By.ID, value="MainContent_ddlTestSiteId")) # Select test site
    sitesSelect.select_by_visible_text("Nassau CC CDL")

    driver.find_element(By.ID, value="btnScheduleBookings").click() # Click schedule bookings button

    try:
        # Wait for the element to be visible and interactable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "txtCidDlgCid1"))
        )
        # Clear the input field
        driver.find_element(By.ID, value="txtCidDlgCid1").clear()
        driver.find_element(By.ID, value="txtCidDlgCid1").send_keys("910840069") # Enter CID
    except TimeoutException:
        print("Timeout: Element 'txtCidDlgCid1' not interactable after waiting.")
    except Exception as e:
        print(f"Exception occurred: {e}")

    driver.find_element(By.ID, value="txtCidDlgDob1").clear() # Clear DOB field    
    driver.find_element(By.ID, value="txtCidDlgDob1").send_keys("06/29/1988") # Enter DOB
    cdlClassSelect = Select(driver.find_element(by=By.ID, value="ddlCidDlgTestType1")) # Select CDL class
    cdlClassSelect.select_by_visible_text("CDL A (Class A CDL)")

    try:
        # Wait for the element to be visible and interactable
        WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.ID, "chkClientInfoDlg"))
        )        
        driver.find_element(By.ID, value="chkClientInfoDlg").click() # Click client info checkbox
    except TimeoutException:
        print("Timeout: Element 'chkClientInfoDlg' not interactable after waiting.")
    except Exception as e:
        print(f"chkClientInfoDlg Exception occurred: {e}")

    # btnClientInfoDlgCheckEligibility
    driver.find_element(By.ID, value="btnClientInfoDlgCheckEligibility").click()

    okMsg  = driver.find_element(By.ID, value="MainContent_vsClientInfoDlgOkMsg")
    errMsg = driver.find_element(By.ID, value="MainContent_vsClientInfoDlgErrMsg")

    # MainContent_vsClientInfoDlgErrMsg
    # MainContent_vsClientInfoDlgOkMsg

    try:
        # Wait for the element to be visible and interactable
        print ("Checking for All CIDs are eligible")
        WebDriverWait(driver, 60).until(
            EC.text_to_be_present_in_element((By.ID, "MainContent_vsClientInfoDlgOkMsg"), "All CIDs are eligible")
        )
        print ("Found text - All CIDs are eligible. Proceeding")   
        driver.find_element(By.ID, value="btnClientInfoDlgContinue").click() # Click to continue
    except TimeoutException:
        print("Timeout: Element 'MainContent_vsClientInfoDlgOkMsg' cannot find such text.")
    except Exception as e:
        print(f"MainContent_vsClientInfoDlgOkMsg Exception occurred: {e}")    

except Exception as e:
    print(f"Exception occurred: {e}")

time.sleep(300)
driver.quit()

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
