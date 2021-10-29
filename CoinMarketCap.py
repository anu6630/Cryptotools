#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from googlesearch import search
import re
import threading
from flask import Flask
from flask import request


# In[2]:


options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')


# In[3]:


driver = webdriver.Chrome("chrome_drivers/chromedriver.exe",chrome_options=options) # Specify the path to the chromedriver here


# In[4]:


driver.execute_script("window.open('about:blank',  '1tab');")
driver.execute_script("window.open('about:blank',  '2tab');")
driver.execute_script("window.open('about:blank',  '3tab');")
driver.execute_script("window.open('about:blank',  '4tab');")
driver.execute_script("window.open('about:blank',  '5tab');")


# In[5]:


used_tabs = []


# In[6]:


_key_lock = threading.Lock()


# In[7]:


def findUnUsedTab():
       # Increasing the counter with lock
       exists = False
       print("Used tabs=")
       print(used_tabs)
       _key_lock.acquire()
       freeTab = None
       print("Lock Aquired")
       for num in [1,2,3,4,5]:
           exists = num in used_tabs
           print("Exists =")
           print(exists)
           if(not exists):
               print("tab not found in list")
               freeTab = num
               print("returning num as free tab = " + str(num))
               break
       _key_lock.release()
       print("Tab " + str(freeTab) + " is free now, Released lock")
       return freeTab


# In[8]:


def markUsedTab(tabId):
    _key_lock.acquire()
    exists = tabId in used_tabs
    if(not exists) :
        print(str(tabId) + " is not there in tabs adding ")
        used_tabs.append(tabId)
    _key_lock.release()


# In[9]:


def markUnusedTab(tabId):
    _key_lock.acquire()
    exists = tabId in used_tabs
    if(exists) :
        print(str(tabId) + " is  there in tabs removing ")
        used_tabs.remove(tabId)
    _key_lock.release()


# In[10]:


def getSourceInNewTab(url):
    tabId = None
    while(True):
        tabId = findUnUsedTab()
        if(tabId>0):
            break
    
    markUsedTab(tabId)
    driver.switch_to.window(str(tabId) +"tab")
    driver.get(url)
    source = driver.page_source
    markUnusedTab(tabId)
    return source


# In[11]:


def getCoinUrlFromGoogle(coinName):
    query = "site:https://coinmarketcap.com/currencies " + coinName
    urls = []
    for j in search(query, tld="com", num=10, stop=10, pause=2):
        urls.append(j)
    coinUrl = urls[0]
    print("Coinurl = " + coinUrl)
    return coinUrl


# In[12]:


def getMarketCapFromSource(source):
    #print("source")
    #print(source)
    soup = BeautifulSoup(source)
    elements = soup.select("div[class*=statsBlockInner]")
    values = {}
    for ele in elements :
        labels = ele.select("div[class*=statsLabel]")
        tag = None 
       
        for label in labels :
            print(label)
            if "Market Cap" == label.getText().strip():
                tag = 1
            elif "Fully Diluted Market Cap" == label.getText().strip():
                tag = 2
            elif "Volume" in label.getText().strip() and not "Market Cap" in label.getText().strip():
                tag = 3
        if (tag == 1) :
            mcapNode = ele.select("div[class*=statsValue]")[0]
            #print("New " + mcapNode.prettify())
            marketCap = mcapNode.getText().replace(",",'').replace("$",'')
            print("marketCap=" + str(marketCap))
            values["marketCap"] = marketCap
        elif (tag ==2):
            mcapNode = ele.select("div[class*=statsValue]")[0]
            #print("New " + mcapNode.prettify())
            marketCap = mcapNode.getText().replace(",",'').replace("$",'')
            print("DilutedmarketCap=" + str(marketCap))
            values["dilutedMarketCap"] = marketCap
        elif (tag == 3):
            mcapNode = ele.select("div[class*=statsValue]")[0]
            #print("New " + mcapNode.prettify())
            marketCap = mcapNode.getText().replace(",",'').replace("$",'')
            print("volume=" + str(marketCap))
            values["volume"] = marketCap
    return values


# In[13]:


def getMarketCap(coinName):
    coinUrl = getCoinUrlFromGoogle(coinName)
    source = getSourceInNewTab(coinUrl)
    data = getMarketCapFromSource(source)
    data["url"] = coinUrl
    return data


# In[ ]:


app = Flask(__name__)
@app.route('/marketcap/')
def marketCap():
    result = {}
    print("Request args=")
    print(request.args)
    coinName = request.args.get('coin')
    result["data"] = getMarketCap(coinName)
    return result
app.run(port=8010)


# In[ ]:




