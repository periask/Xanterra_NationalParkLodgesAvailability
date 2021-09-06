# Xanterra - National Park Lodges Availability
This script is to find the availability of the hotels inside the National Parks in a given month.

# Installation
## Web driver
## Python modules

# Configuration
Update this info in the json file to send the mail with the availability correctly.
```json
"sender": "sender@gmail.com",
"password": "password",
"recipients": ["recipient01@gmail.com"],
"mailserver": "smtp.gmail.com:587",
```

Update the following in each "xanterra" block to match your needs,
```json
"date": 16,
"month": 10,
"year": 2021,
"adults": 2,
"children": 1,
"nights": 1,
```
Please make sure that the date, month and year combination is in the future.


# How to run
```bash
python3 Xanterra_availability.py NPSinfo.json
```
