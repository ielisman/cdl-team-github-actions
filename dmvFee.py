import argparse
#import base64
#import road_test_constants as const
#import firebase_admin
import json
import os
import time
import undetected_chromedriver as uc

from Crypto.PublicKey                   import RSA
from Crypto.Cipher                      import PKCS1_OAEP
from datetime                           import timedelta, date, datetime
#from firebase_admin                     import credentials, firestore
from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

#chromeOptions = webdriver.ChromeOptions()
#driver = uc.Chrome(headless=False, use_subprocess=True, options=chrome_options, version_main=130) # headless=False,


# chromeOptions.add_argument("--disable-gpu")
# chromeOptions.add_argument("--no-sandbox")
# chromeOptions.add_argument("--disable-setuid-sandbox")

# #chromeOptions.add_argument("--incognito") #
# chromeOptions.add_argument("--ignore-certificate-errors")
# chromeOptions.add_argument("--disable-extensions")
# chromeOptions.add_argument("--dns-prefetch-disable")
# #chromeOptions.add_argument("start-maximized") #
# chromeOptions.add_argument('--ignore-ssl-errors=yes')
# #chromeOptions.add_argument("--disable-popup-blocking") #
# chromeOptions.add_argument("--disable-notifications")
# chromeOptions.add_argument('--disable-dev-shm-usage')

#chromeOptions.add_argument('--user-agent="Mozilla/132.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.91 Safari/537.36"')

# print("CAPABILITIES --\n")
# print (driver.capabilities)
# print("\nOPTIONS -- \n")
# print (driver.options.arguments)

chromeOptions = uc.ChromeOptions()
chromeOptions.headless = True
chromeOptions.add_argument("--headless=new")  # Updated argument for headless mode
chromeOptions.add_argument("--no-sandbox")
chromeOptions.add_argument("--disable-dev-shm-usage")
chromeOptions.add_argument("--disable-gpu")

#chromeOptions.add_argument("start-maximized")
#chromeOptions.add_argument("disable-infobars")
#chromeOptions.add_argument("--disable-extensions")

chromeOptions.add_argument("--disable-blink-features")
chromeOptions.add_argument("--disable-blink-features=AutomationControlled")
chromeOptions.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36")
driver = uc.Chrome(options=chromeOptions, use_subprocess=True, version_main=130)

driver.implicitly_wait(30)
driver.set_page_load_timeout(30)

try:
    
    retries = 3
    attempt = 0
    site = "https://transact3.dmv.ny.gov/skillstestpayment/" # "https://nowsecure.nl"
    while attempt < retries:
        try:
            print (f"Retrieving site {site}. Attempt {attempt+1}")
            driver.get(site)                            
            break
        except Exception as e0:
            print(f"Unable to retrieve {site}: {e0}")
            #driver.reconnect()
            #driver.refresh()
            attempt += 1
            time.sleep(1)
    else:
        print(f"Unable to retrieve {site} after {attempt} attempts")
        driver.quit()
        exit(0)

    print("Student form")

    WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.ID, "sClientID") ))
    driver.find_element(by=By.ID, value="sClientID").clear()
    driver.find_element(by=By.ID, value="sClientID").send_keys("880748593")  # 418079953
    Select(driver.find_element(by=By.ID, value="sDOBMonth")).select_by_value("06") # 02
    Select(driver.find_element(by=By.ID, value="sDOBDay")).select_by_value("28") # 15
    driver.find_element(by=By.ID, value="sDOBYear").clear()
    driver.find_element(by=By.ID, value="sDOBYear").send_keys("1987") # 1997
    driver.find_element(by=By.ID, value="sCDL").click()
    driver.find_element(by=By.ID, value="sEmailAddress").clear()
    driver.find_element(by=By.ID, value="sEmailAddress").send_keys("redhookcdl@gmail.com")  
    driver.find_element(by=By.ID, value="sEmailAddress2").clear()
    driver.find_element(by=By.ID, value="sEmailAddress2").send_keys("redhookcdl@gmail.com")
    # s = driver.find_element(by=By.NAME, value="submit order")    
    
    print("Filled out student form")
    driver.find_element(by=By.NAME, value="frmGetDrvInfo").submit()
    
    print("Verifying student form")
    try: 
        WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.NAME, "btnPrevious") ))
    except Exception as e1:
        print("Unable to verify student form")
    driver.find_element(by=By.NAME, value="frmVerify").submit() #by=By.NAME, value="submit order"

    print("Entering payment form")
    try:
       WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.XPATH, "//button[@id='id_checkout']/div") ))
    except Exception as e2:
       print("Unable to enter payment form")
    ###################### WORKS FINE UNDER DIFFERENT ENV: 

    #driver.find_element(by=By.NAME, value="id_checkout").click()
    #id_checkout
    driver.find_element(by=By.XPATH, value="//button[@id='id_checkout']/div").click()    
    
    print("Payment form")
    driver.find_element(by=By.ID, value="ssl_card_number").clear()
    driver.find_element(by=By.ID, value="ssl_card_number").send_keys("$CN")
    driver.find_element(by=By.ID, value="ssl_exp_date").clear()
    driver.find_element(by=By.ID, value="ssl_exp_date").send_keys("$CE")
    driver.find_element(by=By.ID, value="ssl_cvv2cvc2").clear()
    driver.find_element(by=By.ID, value="ssl_cvv2cvc2").send_keys("$CV")    
    driver.find_element(by=By.ID, value="ssl_first_name").clear()
    driver.find_element(by=By.ID, value="ssl_first_name").send_keys("$FN")
    driver.find_element(by=By.ID, value="ssl_last_name").clear()
    driver.find_element(by=By.ID, value="ssl_last_name").send_keys("$LN")
    # driver.find_element(by=By.XPATH, value="//ng-include[@id='id_section_billing']/div[3]/div/div[2]/md-input-container").click()    
    driver.find_element(by=By.ID, value="ssl_avs_address").clear()
    driver.find_element(by=By.ID, value="ssl_avs_address").send_keys("$ADDRESS_STREET")
    driver.find_element(by=By.ID, value="ssl_city").clear()
    driver.find_element(by=By.ID, value="ssl_city").send_keys("$ADDRESS_CITY")
    driver.find_element(by=By.ID, value="ssl_state").clear()
    driver.find_element(by=By.ID, value="ssl_state").send_keys("$ADDRESS_STATE")
    driver.find_element(by=By.ID, value="ssl_avs_zip").clear()
    driver.find_element(by=By.ID, value="ssl_avs_zip").send_keys("$ADDRESS_ZIP")
    # driver.find_element(by=By.NAME, value="pmtFormCtrl.pmtForm").submit() 
    #driver.find_element(by=By.XPATH, value="//div[@id='id_main_left']/ng-include/div/div/form/div/div/div").click()
    #driver.find_element(by=By.XPATH, value="//div[@id='id_main_left']/ng-include/div/div/form/div/div/div").submit()


    #driver.find_element(by=By.XPATH, value="//button[@id='id_recaptcha']/div[1]/div[1]").click()
    print("Payment form is submitted")

    ##### POST RESULT
    # //*[@id="div-container"]/div/div[2]/div/div[1]  (/html/body/div[1]/div[5]/div/div[2]/div/div[1])
    #div-container > div > div.container.ml-4 > div > div:nth-child(1)
    #document.querySelector("#div-container > div > div.container.ml-4 > div > div:nth-child(1)")
    # Order Number: 20241030-0082170  
    
except Exception as e:
    print(f"Exception occurred: {e}") 

time.sleep(50)
driver.quit()

# chrome_options.add_argument('--headless') 
#chrome_options.add_argument('--disable-dev-shm-usage')
# options.add_argument("start-maximized")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)
#chromeOptions.addArguments("--headless")

#chromeOptions.add_argument("--disable-blink-features")
#chromeOptions.add_argument("--disable-blink-features=AutomationControlled")

#chromeOptions.add_argument("start-maximized")
#chromeOptions.add_argument("--incognito")
# ensure that version_main=Current browser version is 130.0.6723.59 (first numbers before .)

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chromeOptions)

#driver.implicitly_wait(30)
#driver.set_page_load_timeout(10)
# driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
# driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
#print(driver.execute_script("return navigator.userAgent;"))

# params = {
#     "source": "Object.defineProperty(navigator, 'webdriver', { get: () => undefined })"
# }

# driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", params)

# el = driver.find_element(by=By.XPATH, value="/html/body/div[1]/div[5]/div/form/div[1]/div[1]/div/div[2]/input")
# el.clear()
# el.send_keys("559471288")