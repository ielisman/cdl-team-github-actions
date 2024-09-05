import time

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
    driver.get("https://www.nyakts.com/Login.aspx?mid=2269") # "https://www.nyakts.com/Login.aspx?ReturnUrl=%2fNyRstApps%2fThirdPartyBooking.aspx%3fmid%3d2269&mid=2269"
    # driver.get("https://www.nyakts.com/NyRstApps/ThirdPartyBooking.aspx?mid=2269")    
    driver.find_element(by=By.ID, value="UserName").clear()
    driver.find_element(by=By.ID, value="Password").clear()
    driver.find_element(by=By.ID, value="UserName").send_keys("7583ds")    
    driver.find_element(by=By.ID, value="Password").send_keys("Ditmas2025!")
    driver.find_element(by=By.ID, value="Login1_btnPreLoginButton").click()

    cancelOtherSession = False
    try:
        loginContinueMessage = driver.find_element(by=By.ID, value="continueMessage")        
        if loginContinueMessage.text == "If you continue, their session will be lost. Would you like to continue?":
            print(f"Found loginContinueMessage {loginContinueMessage.text}")
        driver.find_element(by=By.ID, value="confirmDialog").click()
        print(f"Found existing session. Cancelling it")        
        cancelOtherSession = True
    except Exception as es:
        print(f"No session to cancel. Continuing")
        
    driver.get("https://www.nyakts.com/NyRstApps/ThirdPartyBooking.aspx?mid=2269")

    driver.switch_to.default_content()
    driver.switch_to.frame(driver.find_element(By.XPATH, value=".//iframe[@title='reCAPTCHA']"))
    driver.find_element(By.ID, value="recaptcha-anchor-label").click()    
    # try:
    #     WebDriverWait(driver, 10).until(
    #         EC.text_to_be_present_in_element_attribute(
    #             (By.ID, "recaptcha-anchor"), 
    #             "aria-checked", 
    #             "true")
    #     )
    # except:
    #     print(f"Recaptcha is not checked")   
    # ariaChecked = recaptchaCheckBox.get_attribute(name="aria-checked")    
    
    driver.switch_to.default_content()

    
    # here we can interfere by hand in case captcha appears
    # we will check for the element of captcha. if exists, we will explicitely wait until it is solved
    sitesSelect = Select(driver.find_element(by=By.ID, value="MainContent_ddlTestSiteId"))
    sitesSelect.select_by_visible_text("Nassau CC CDL")

    driver.find_element(By.ID, value="btnScheduleBookings").click()
    driver.find_element(By.ID, value="txtCidDlgCid1").clear()
    driver.find_element(By.ID, value="txtCidDlgDob1").clear()
    driver.find_element(By.ID, value="txtCidDlgCid1").send_keys("153704637")
    driver.find_element(By.ID, value="txtCidDlgDob1").send_keys("04/20/1970")

    cdlClassSelect = Select(driver.find_element(by=By.ID, value="ddlCidDlgTestType1"))
    cdlClassSelect.select_by_visible_text("CDL A (Class A CDL)")

    

except Exception as e:
    print(f"Exception occurred: {e}")
time.sleep(90)
#title = driver.title
#print("Enroll was simulated")
#print(title)

# driver.quit()
