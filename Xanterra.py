#!/usr/bin/env python3

import sys
import json
import time
import datetime
import tabulate
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def create_firefox_driver():
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    return driver

def wait_for_page_load(driver, url):
    print("URL:", url)
    driver.get(url)

    timeout = 10
    try:
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'day-row-wrapper'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")
        sys.exit(1)

    return driver

def get_hotel_names(driver):
    hotels = []
    hotels_title_elements = driver.find_elements_by_class_name('hotel-title')
    for hte in hotels_title_elements:
        hotels.append(hte.text)

    # print(hotels)
    return hotels

def get_all_availability(driver):
    availability = {}
    days = driver.find_elements_by_class_name('day-row-wrapper')
    tabledata = []
    available_hotels_index = []

    for d in days:
        date = d.find_element_by_class_name('day')
        date = " ".join(date.text.split())
        index = 0
        is_available = False

        price = [date]
        price_cell = d.find_elements_by_class_name("price-cell")
        for pc in price_cell:
            s = pc.find_element_by_xpath(".//span")
            if s.get_attribute("class") not in ["closed", "sold-out"]:
                is_available = True
                price.append(s.text)
                if index not in available_hotels_index:
                    available_hotels_index.append(index)

                if hotels[index] not in availability.keys():
                    availability[hotels[index]] = {"dates": []}
                availability[hotels[index]]["dates"].append("{} - {}".format(date, s.text))
            else:
                price.append("")

            index += 1
        if is_available:
            tabledata.append(price)

    # print(json.dumps(availability, indent=2))
    return availability, tabledata, available_hotels_index

def close_browser(driver):
    if driver != None:
        driver.close()

def send_mail(npsdata, mail_text, mail_html):
    html = """
<html><head><style>
    table, td, th { border: 1px solid black; }
    table { width: 100%; border-collapse: collapse; }
    </style> </head>
"""
    html_body = """
    <body> {} </body> </html>
"""
    text = """
{}
"""

    message = MIMEMultipart("alternative", None, [MIMEText(text.format(mail_text)),
                                                  MIMEText(html+ html_body.format(mail_html),'html')])
    dt = datetime.datetime.now()

    message['Subject'] = "National Park Lodges Availability - {}".format(dt.strftime("%m-%d-%Y %H:%M:%S %Z %z"))
    message['From'] = npsdata["sender"]
    message['To'] = ",".join(npsdata["recipients"])
    server = smtplib.SMTP(npsdata["mailserver"])
    server.ehlo()
    server.starttls()
    server.login(npsdata["sender"], npsdata["password"])
    server.sendmail(npsdata["sender"],
                    npsdata["recipients"],
                    message.as_string())
    server.quit()

if __name__ == "__main__":
    driver = None

    with open(sys.argv[1]) as xfp:
        data = json.load(xfp)

    old_message = ""

    while True:
        message = ""
        mail_text = ""
        mail_html = ""

        for x in data["xanterra"]:
            if len(message):
                message += message + "\n\n"
            message += "{}{}:\n".format(message, x["NP"])
            url = x["url"].format(x["month"],
                                  x["date"],
                                  x["year"],
                                  x["adults"],
                                  x["children"],
                                  x["nights"])
            driver = wait_for_page_load(create_firefox_driver(), url)
            hotels = get_hotel_names(driver)
            availability, tabledata, available_hotels_index = get_all_availability(driver)

            for hotel in availability:
                message += "{}\n{} - {}".format(message, hotel, ", ".join(availability[hotel]["dates"]))


            for i in range(len(hotels)-1, -1, -1):
                if i not in available_hotels_index:
                    del hotels[i]
                    for j in range(len(tabledata)):
                        del tabledata[j][i+1]

            if len(mail_html):
                mail_html += "<br><br>"
                mail_text += "\n\n"

            mail_html += "<b>" + x["NP"] + "</b><br>"
            mail_text += x["NP"] + "\n"

            mail_text += tabulate.tabulate(tabledata,
                                           ["Dates"]+hotels,
                                           tablefmt="fancy_grid")
            mail_html += tabulate.tabulate(tabledata,
                                           ["Dates"]+hotels,
                                           tablefmt="html")
        if len(message) and old_message != message:
            print(mail_text)
            old_message = message
            send_mail(data, mail_text, mail_html)

        close_browser(driver)
        time.sleep(60)
