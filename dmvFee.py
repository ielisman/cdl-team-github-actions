import argparse
import base64
import road_test_constants as const
import firebase_admin
import json
import os
import time
import undetected_chromedriver as uc

from Crypto.PublicKey                   import RSA
from Crypto.Cipher                      import PKCS1_OAEP
from datetime                           import timedelta, date, datetime
from firebase_admin                     import credentials, firestore
from selenium                           import webdriver
from selenium.common.exceptions         import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service  import Service
from selenium.webdriver.common.by       import By
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.support.ui      import WebDriverWait, Select
from webdriver_manager.chrome           import ChromeDriverManager

chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_argument("--disable-gpu")
chromeOptions.add_argument("--no-sandbox")
chromeOptions.add_argument("--disable-setuid-sandbox")
chromeOptions.add_argument('--disable-dev-shm-usage')
driver = uc.Chrome(headless=False,use_subprocess=True, options=chromeOptions, version_main=130)

try:
    
    driver.get("https://transact3.dmv.ny.gov/skillstestpayment/")
    WebDriverWait(driver, 20).until_not (EC.invisibility_of_element ( (By.ID, "sClientID") ))
    driver.find_element(by=By.ID, value="sClientID").clear()
    driver.find_element(by=By.ID, value="sClientID").send_keys("559471288")
    Select(driver.find_element(by=By.ID, value="sDOBMonth")).select_by_value("11")
    Select(driver.find_element(by=By.ID, value="sDOBDay")).select_by_value("14")
    driver.find_element(by=By.ID, value="sDOBYear").clear()
    driver.find_element(by=By.ID, value="sDOBYear").send_keys("1988")
    driver.find_element(by=By.ID, value="sCDL").click()
    driver.find_element(by=By.ID, value="sEmailAddress").clear()
    driver.find_element(by=By.ID, value="sEmailAddress").send_keys("redhookcdl@gmail.com")
    driver.find_element(by=By.ID, value="sEmailAddress2").clear()
    driver.find_element(by=By.ID, value="sEmailAddress2").send_keys("redhookcdl@gmail.com")
    # #driver.find_element_by_name("submit order").click()
    # driver.find_element_by_name("submit order").click()
    # #driver.get("https://api.convergepay.com/hosted-payments/")
    # driver.find_element_by_xpath("//button[@id='id_checkout']/div").click()
    # #driver.find_element(by=By.ID, value="ssl_card_number").click()
    # driver.find_element(by=By.ID, value="ssl_card_number").clear()
    # driver.find_element(by=By.ID, value="ssl_card_number").send_keys("")
    # #driver.find_element(by=By.ID, value="ssl_exp_date").click()
    # driver.find_element(by=By.ID, value="ssl_exp_date").clear()
    # driver.find_element(by=By.ID, value="ssl_exp_date").send_keys("")
    # #driver.find_element(by=By.ID, value="ssl_cvv2cvc2").click()
    # driver.find_element(by=By.ID, value="ssl_cvv2cvc2").clear()
    # driver.find_element(by=By.ID, value="ssl_cvv2cvc2").send_keys("648")
    # #driver.find_element(by=By.ID, value="ssl_first_name").click()
    # driver.find_element(by=By.ID, value="ssl_first_name").clear()
    # driver.find_element(by=By.ID, value="ssl_first_name").send_keys("Igor")
    # driver.find_element(by=By.ID, value="ssl_last_name").clear()
    # driver.find_element(by=By.ID, value="ssl_last_name").send_keys("Elisman")
    # driver.find_element(by=By.XPATH, value="//ng-include[@id='id_section_billing']/div[3]/div/div[2]/md-input-container").click()
    # #driver.find_element(by=By.ID, value="ssl_avs_address").click()
    # driver.find_element(by=By.ID, value="ssl_avs_address").clear()
    # driver.find_element(by=By.ID, value="ssl_avs_address").send_keys("201 Ditmas Ave")
    # driver.find_element(by=By.ID, value="ssl_city").clear()
    # driver.find_element(by=By.ID, value="ssl_city").send_keys("Brooklyn")
    # driver.find_element(by=By.ID, value="ssl_state").clear()
    # driver.find_element(by=By.ID, value="ssl_state").send_keys("NY")
    # driver.find_element(by=By.ID, value="ssl_avs_zip").clear()
    # driver.find_element(by=By.ID, value="ssl_avs_zip").send_keys("11218")
    #driver.find_element_by_xpath("//div[@id='id_main_left']/ng-include/div/div/form/div/div/div").click()
except Exception as e:
    print(f"Exception occurred: {e}") 

time.sleep(30)
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