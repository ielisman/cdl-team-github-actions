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

print (f"Opening {os.getenv('GITHUB_ENV')} environment variables file and writing new variables to that")
env_file = os.getenv('GITHUB_ENV') # Get the path of the runner file
with open(env_file, "a") as repo_env_file:
  repo_env_file.write(f"TITLE='{title}'\n")
  repo_env_file.write(f"TEST123='TESTOK123'\n")
  repo_env_file.write(f"RUNRESULT='title={title}'\n")
  print(f"wrote TITLE='{title}'\n")
  print(f"wrote TEST123='TESTOK123'\n")
  print(f"wrote RUNRESULT='title={title}'\n")

  # Print the website title to the console
print(f"title={title}; URL={os.environ['URL']}; LOGIN={os.environ['LOGIN']}; ")

# Close the webdriver
driver.quit()
