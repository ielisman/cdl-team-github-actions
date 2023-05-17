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

with open(os.getenv('GITHUB_ENV'), "a") as repo_env_file:
  repo_env_file.write(f"TITLE={title}\n")
  repo_env_file.write(f"URL={os.environ['URL']}\n")
  repo_env_file.write(f"LOGIN={os.environ['LOGIN']}\n")

# Close the webdriver
driver.quit()
