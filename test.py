from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import sys
import os

url = ""
if (len(sys.argv) > 2):
  url = sys.argv[2]
else:
  print("URL is not supplied. Quiting")
  quit()

# Configure Chrome options for headless mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')

# Initialize the Chrome webdriver with WebDriver Manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Navigate to the website URL
driver.get(url)

# Retrieve the website title
title = driver.title

env_file = os.getenv('GITHUB_ENV') # Get the path of the runner file
with open(env_file, "a") as env_file:
  env_file.write(f"TITLE={title}")
  env_file.write(f"TEST123=TESTOK123")
  env_file.write(f"RUNRESULT='title={title}'")
 
# Print the website title to the console
print(f"title={title}; URL={os.environ['URL']}; LOGIN={os.environ['LOGIN']}; ")

# Close the webdriver
driver.quit()
