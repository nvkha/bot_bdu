from bs4 import BeautifulSoup
import requests
import re
from datetime import date, datetime
import os 
from helper import regex_date



def getFile(url, name):  
    # Download pdf file from url
    r = requests.get(url, stream=True)

    with open(os.path.join(os.getcwd(), f'{name}.pdf'), 'wb') as f:
        f.write(r.content)
        return name

def crawl(name):
    url = "https://camau.bdu.edu.vn/chuyen-muc/sinh-vien/chinh-quy"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    href = ''

    # Tìm link lịch học tuần mới nhất
    for link in soup.find_all('a'):
        if link.get("title"):
            if "Lịch học tuần" in link.get("title"):
                    href = link.get("href")
                    break
    
    # Truy cập link lịch học và download file pdf
    response = requests.get(href)
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all('a'):
        if re.search("pdf$", link.get('href')): 
             getFile(link.get('href'), name)
             return name

def lastestSchedule():
    url = "https://camau.bdu.edu.vn/chuyen-muc/sinh-vien/chinh-quy"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    href = ''

    # Tìm link lịch học tuần mới nhất
    for link in soup.find_all('a'):
        if link.get("title"):
            if "Lịch học tuần" in link.get("title"):
                    return regex_date(str(link.get('title'))).isocalendar()[1]

    
             

