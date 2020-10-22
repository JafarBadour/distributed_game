#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# -*- coding: utf-8 -*-
"""
Website(s) Scraper
Version 1.0.2

Revision Notes:
1.0.0 (10/12/2020) - Initial
1.0.1 (10/14/2020) - Added headers for possible new article title
1.0.2 (10/16/2020) - Added structure to accomodate unlimited number of sites

"""
###############################################################################
# Import required libraries
import csv
from lxml import html
import os
import requests
from sys import exit
import time
import traceback

###############################################################################
# Required variables for scraper
# Set number of seconds to look at website again for new articles
WAIT_SECONDS = 10

# Set file to be used to put new ticker symbol signals
SIGNALS_FILE = "Website_Signals.txt"

# Files for symbol-company name lists
STOCK_NAME_FILES = ["AMEX.txt", "NASDAQ.txt", "NYSE.txt"]

# List of (abbrev, site) tuples to process
SITES = [
    ('HR', 'https://hindenburgresearch.com'),
    ]

# list to populate with titles that are not processed correctly
UNPROCESSED_LIST = []
REMOVE_LIST = ["ltd.", "ltd", "inc.", "inc", "plc.", "plc", "corp.", "corp"]


# In[ ]:


# # run this in terminal
# !sudo apt install nordvpn
# !sudo nordvpn connect
# # usersname= "aleksandar.abas@gmail.com"
# # password= "Gangsta88*"


# In[ ]:




###############################################################################
def parse_tickers():
    """Get list of symbol, company names list from all input files."""
    master_data = [['Symbol', 'Description']]
    # Loop through files
    for file in STOCK_NAME_FILES:
        try:
            # Read file
            with open(file, newline='') as f:
                reader = csv.reader(f, delimiter='\t')
                data = list(reader)
            master_data = master_data + data[1:]
        except Exception:
            print('Error reading {}!!!'.format(file))
    print('{} symbols/companies found'.format(len(master_data)-1))
    return master_data





# In[ ]:


###############################################################################
def get_articles():
    # Loop through the desired websites
    for abbrev, site in SITES:
        processed, r = prepare_iteration(abbrev, site)
        tree = html.fromstring(r.content.decode('utf-8'))

        # Check for appropriate site based on abbrev
        if abbrev == 'HR':
            # Process all titles on page
            titles = tree.xpath('//h2[@class="post-title"]/a/text()')
            # Add header to title (when one)
            header = tree.xpath('//div[@class="post-heading"]/h1/a/text()')
            if header:
                for head in header:
                    titles.append(head)

        # Loop through titles, if any
        if titles:
            for title in titles:
                # Process any articles that have not already been processed
                if title not in processed:
                    pass
                    #process_new_article(abbrev, title)



# In[ ]:


###############################################################################
def process_new_article(abbrev, title):
    try:
        title_info = []
        company = None
        symbol  = None

        print("\n\nNew {} article/company: {}".format(abbrev, title))
        print('Checking for company and symbol for the article')

        # Loop through ticker/companies in master list
        for sym, co in tickers_companies:
            # First remove any undesired words from the co name
            result_words = [word for word in co.split()                             if word.lower() not in REMOVE_LIST]
            result = ' '.join(result_words)


            # Check for company name in title / max 4 words
            if len(title.split(':')[0].split()) < 5:
                #title_info.append(title.split(':')[0])
                company = title.split(':')[0]
                if company in co:
                    print('Company name ({}) at beginning of title'.format(
                        company))
                    symbol = sym
                    title_info.append(company+" / "+symbol)
                    break
                elif company == sym:
                    print('Ticker symbol ({}) at beginning of title'.format(
                        company))
                    symbol = sym
                    title_info.append(company+" / "+symbol)

            # Check for ticker in title
            if ' ' + sym in title and len(sym) > 1:
                print('Symbol ({}) in title'.format(sym))
                symbol = sym
                company = co
                title_info.append(company+" / "+symbol)
                break
            # Check for company in title
            if co.lower() in title.lower() and len(co) > 4:
                print('Company name ({}) in title'.format(co))
                symbol = sym
                company = co
                title_info.append(company+" / "+symbol)
                break

        if title_info:
            print("Tickers/companies related: \t\t{}".format(
                ', '.join(title_info)))
            # Add symbol to list for new signals
            if symbol is not None:
                save_symbol(abbrev, symbol)
        else:
            print("No known tickers/companies found for the title")
            UNPROCESSED_LIST.append((abbrev + "/ " + title))
        print('\n')

        # Save title to list of processes titles
        save_title(abbrev, title)
    except Exception:
        print(traceback.format_exc())


###############################################################################


# In[ ]:


def save_symbol(abbrev, symbol):
    try:
        f = open(SIGNALS_FILE, "a")
        f.write("\n"+symbol+', '+abbrev)
        f.close()
    except Exception:
        print(traceback.format_exc())


# In[ ]:


###############################################################################
def save_title(abbrev, title):
    file = 'processed_' + abbrev + '.txt'
    try:
        f = open(file, "a")
        f.write(title + '\n')
        f.close()
    except Exception:
        print(traceback.format_exc())


# In[ ]:


###############################################################################
def prepare_iteration(abbrev, site):
    file = 'processed_' + abbrev + '.txt'
    if os.path.exists(file):
        with open(file, 'r') as  f:
            processed = f.readlines()
            processed = [x.strip() for x in processed]
    else:
        processed = []
        print("The {} script is running for first time".format(abbrev))
    r = requests.get(site)
    return processed, r

class IpChanger:
    def __init__(self):
        self.countries  = ['uk', 'france', 'germany', 'us', 'italy', 'portugal', 'canada', 'norway']
        self.password = 'bakhetle' # if you are running on aws just leave empty ''
    def connect2newIP(self):
        import random 
        
        import subprocess
        from subprocess import run, PIPE
        
        country_of_choice = random.choice(self.countries)
        bash_command = f'echo {self.password} | sudo -S nordvpn connect {country_of_choice}'
        # 'Put your credentials in a normal terminal instance {login, password} then run this'
        self.process = subprocess.Popen(
            bash_command,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.process.wait() # you can delete this condition and use IpChanger::killNordvpn
        print('\n', 'ip changed successfully, you hacked them soldier!!')
        
    def killNordvpn(self):
        subprocess.Popen.kill(self.process)
    
    def block_and_wait(self):
        self.process.wait()


# In[ ]:



###############################################################################
if __name__ == '__main__':
    #tickers_companies = parse_tickers()
    
    count = 0
    print('Running, delay between checks = {}s'.format(WAIT_SECONDS))
    print('Will print message every 10 minutes or on new signal')
    # Update every 10 minutes or 600s
    update_int = int(600/WAIT_SECONDS)
    error_counter = 0
    while True:
        if error_counter == 2:
            IpChanger().connect2newIP()
        try:
            get_articles()
            count += 1
            if count == update_int:
                print("Running...10min update")
                count = 0
            time.sleep(WAIT_SECONDS)
            error_counter = 0
        except Exception:
            error_counter += 1
            print(traceback.format_exc())
            print('Error connecting to server, ip banned')


# In[11]:


# import requests, json

# data = json.loads(requests.get("http://ip.jsontest.com/").content)
# print(data["ip"])

