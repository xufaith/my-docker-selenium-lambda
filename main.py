import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info("I'm in")

import requests
import pandas as pd
from bs4 import BeautifulSoup
from supabase import create_client, Client
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from tempfile import mkdtemp
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


def handler(event=None, context=None):
    logger.info("I'm in the function")
    username = "fxu73@gatech.edu"
    password = "[hdph98"
    options = webdriver.ChromeOptions()
    service = ChromeService("/opt/chromedriver/chromedriver")

    options.binary_location = '/opt/chrome/chrome'
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    temp_dir = mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")
    options.add_argument(f"--data-path={temp_dir}/data-path")
    options.add_argument(f"--disk-cache-dir={temp_dir}/cache-dir")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")
    options.add_argument("--mute-audio")
    options.add_argument("--hide-scrollbars")
    options.add_argument("--metrics-recording-only")
    logger.info("made it past all the options stuff")

    driver = webdriver.Chrome(options=options, service=service)
    logger.info("webdriver successfully connected to 'chrome for testing'")
    
    
    loginurl = 'https://eharvest.acfb.org/Login.aspx'
    homeurl = 'https://eharvest.acfb.org/Default.aspx'
    invurl = 'https://eharvest.acfb.org/InventoryView.aspx'
    driver.get(loginurl)
    WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.ID, 'txtUserName')))

    # Entering username
    u_input = driver.find_element(By.ID, 'txtUserName')
    u_input.clear()
    u_input.send_keys(username)
    p_input = driver.find_element(By.ID, 'txtPassword')
    driver.execute_script(f"arguments[0].value='{password}';", p_input)

    # This is how you find & click a button
    login_button = driver.find_element(By.ID, 'btnLogin')
    login_button.click()
    WebDriverWait(driver, 10).until(ec.url_to_be(homeurl))

    #Did a popup for "Reports Due" show
    try:
        x_btn = driver.find_element(By.XPATH, "//span[@class='rwCommandButton rwCloseButton']")
        x_btn.click()
        time.sleep(10)
    except:
        pass
    inv_button = driver.find_element(By.ID, 'mnuMain_btnInventory')
    inv_button.click()
    WebDriverWait(driver, 10).until(ec.url_to_be(invurl))
    logger.info("made it to inventory page")
    ###################################### Got into ACFB Inventory Page #####################################

    # Once logged in, fetch the data
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    header_div = soup.find("div", {"id": "grdData_GridHeader", "class": "rgHeaderDiv"})
    if not header_div:
        raise Exception("Header div not found")
    thead = header_div.find("thead")
    if not thead:
        raise Exception("Thead not found")
    header_row = thead.find("tr")
    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

    data_div = soup.find("div", {"id": "grdData_GridData", "class": "rgDataDiv"})
    if not data_div:
        raise Exception("Data div not found")

    tbody = data_div.find("tbody")
    row_tags = tbody.find_all("tr")
    data = []
    temp_cat = ""
    for row in row_tags:
        cols = row.find_all('td')
        curr = [col.get_text(strip=True) for col in cols]

        if curr[0] != "":
            temp_cat = curr[0]
        else:
            curr[0] = temp_cat
        data.append(curr)

    # Convert data into a pandas dataframe
    df = pd.DataFrame(data, columns=headers)
    logger.info("scraped the inventory table")
    ####################################### End of scraping #######################################

    # Remove nutrition column
    df = df.drop('Nutrition', axis=1)

    # Rename column names to match database
    df.rename(columns={'$': 'cost', 'Cs/Pallet': 'cs_per_pallet', 'Item #': 'item_num', 'Pkg. Info': 'pkg_info'}, inplace=True)

    # Remove unwanted categories
    unwanted_categories = ['Dairy Products', 'Hsehold Cleanng', 'Infant', 'PaperProd', 'Beverages','Bread Products','Snacks']
    df = df[~df['Product Category'].isin(unwanted_categories)]

    # Strip leading/trailing spaces if present
    df = df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

    # Change datatypes
    # Convert the first 5 columns to string
    df.iloc[:, 0:5] = df.iloc[:, 0:5].astype(str)
    # Convert the next 2 columns to int
    df.iloc[:, 5:7] = df.iloc[:, 5:7].apply(lambda x: x.astype(str).str.replace(',', '').astype(int))
    # Convert the next 3 columns to float
    df.iloc[:, 7:10] = df.iloc[:, 7:10].apply(lambda x: x.astype(str).str.replace(',', '').astype(float))

    df = df.reset_index(drop=True)
    logger.info("data cleaned")
    ################################### End of Data Cleaning ##############################################
    # Supabase credentials
    supabase_url = 'https://atmafjrxijoqjphoclzo.supabase.co'
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF0bWFmanJ4aWpvcWpwaG9jbHpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgyNjMxNDAsImV4cCI6MjA1MzgzOTE0MH0.UDfIVdt4hWaIzujfJeRZhXDgoeMe8CjnGdy6Az6aIrc'

    # Initialize the Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Supabase client initialized")

    # Convert NaN values to None (JSON-friendly)
    df= df.where(pd.notna(df), None)
    # Convert dataframe to list of dictionaries to prepare for Supabase
    hist_records = df.to_dict(orient='records')
    logger.info("supabase successfully connected")
    ################################# New Items Identified: ####################################

    # Compare new inventory data with old data in curr_food_bank table
    # Retrieve the old data from the Supabase table
    old_data = supabase.table('curr_food_bank').select('*').execute()
    old_df = pd.DataFrame(old_data.data)

    # Compare the new data with the old data (check for rows not in the old data)
    merged_df = pd.merge(df, old_df, how='left', on=['item_num'], indicator=True)
    newitems_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns='_merge')
    newitems_df = newitems_df[~newitems_df['Description'].str.lower().str.contains('chip')]
    newitems_df = newitems_df[~newitems_df['Description'].str.lower().str.contains('tote')]
    newitems_df = newitems_df[~newitems_df['Description'].str.lower().str.contains('juice')]
    newitems_df = newitems_df[~newitems_df['Description'].str.lower().str.contains('bulk')]

    def text_sam_n_jenny(text):
        resp = requests.post('https://textbelt.com/text', {
            'phone': '4704138842', #Jenny
            'message': text,
            'key': '38b13e8b0b91647a96c032180781475ff4433c8aGGmUsrgjJ9Jpuo9AwOfEgJfA1',
        })
        resp = requests.post('https://textbelt.com/text', {
            'phone': '6789383080', #Sam
            'message': text,
            'key': '38b13e8b0b91647a96c032180781475ff4433c8aGGmUsrgjJ9Jpuo9AwOfEgJfA1',
        })
        return resp
    
    if len(newitems_df) > 0:
        # print("New items added to ACFB since last check:")
        # print(newitems_df)
        item_str = "".join([f"{row['Description']} - {row['Product Category']}\n" for i,row in newitems_df.iterrows()])
        item_str = item_str[:-1]
        message = f"New items available:\n{item_str}"

        if len(message) > 160:
            alist = message.split("\n")
            temp = ""
            i = 0
            while len(temp) < 160 and i < len(alist):
                if (len(alist[i]) + len(temp)) < 160:
                    if i == 0:
                        temp += alist[i]
                    else:
                        temp += "\n" + alist[i]
                else:
                    resp = text_sam_n_jenny(temp)
                    temp = ""
                i += 1
            message = temp

        resp = text_sam_n_jenny(message)
        print(resp.json())
    logger.info("Texts sent")
    ################################# Replacing all data in Postgres ###################################

    # Clearing old data and inserting new data into current table
    # Clear existing data from current table
    def insert_dataframe(table_name, data):
        # Convert column titles to lowercase and spaces to underscores
        data.columns = data.columns.str.lower()
        data.columns = data.columns.str.replace(" ", "_")
        # Convert NaN values to None (JSON-friendly)
        data = data.where(pd.notna(data), None)
        # Convert dataframe to list of dictionaries to prepare for Supabase
        data_records = df.to_dict(orient='records')
        # Insert data to desired table
        try:
            response = (supabase.table(table_name).insert(data_records).execute())
            return response
        except Exception as exception:
            return exception
    # Insert new food bank data into current table
    insert_dataframe('curr_food_bank', df)
    # Find the most recent 'pull_time'
    latest_pull_time = supabase.table('curr_food_bank').select('pull_time').order('pull_time', desc=True).limit(1).execute()
    # Get the latest 'pull_time' from the query result
    latest_pull_time_value = latest_pull_time.data[0]['pull_time']  # Extract the latest pull_time value
    # Delete rows that do not have the most recent pull_time
    supabase.table('curr_food_bank').delete().neq('pull_time', latest_pull_time_value).execute()
    logger.info("Latest foodbank scrape updated in supabase")

    return "Success"
