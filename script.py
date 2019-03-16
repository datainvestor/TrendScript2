import json
import urllib.request
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream 
from bs4 import BeautifulSoup
import requests
import datetime
from pymongo import MongoClient 
from email.mime.text import MIMEText
import smtplib
import os
#from config import *

now = datetime.datetime.now()
api_news= os.environ["api_news"]

#twitter setup
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_SECRET = os.environ["ACCESS_SECRET"]
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
twitter = Twitter(auth=oauth)

#polish
pol_trends = twitter.trends.place(_id = 23424923)
twittrendlistPL=[]
for i in pol_trends[0]['trends']:
    twittrendlistPL.append(i['name'])
strPLT="<br>".join(str(x) for x in twittrendlistPL[0:15])

#global trends
globaltrends=twitter.trends.place(_id = 1)
twittrendlist=[]
for i in globaltrends[0]['trends']:
    twittrendlist.append(i['name'])    
def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True    
G=[i for i in twittrendlist if isEnglish(i)]
strGT="<br>".join(str(x) for x in G[0:15])

#us headlines
url = ('https://newsapi.org/v2/top-headlines?'
       'country=us&'+api_news)
response = requests.get(url)
listus=[]
for i in range(len(response.json()['articles'])):
    listus.append(response.json()['articles'][i]['title'])
    listus.append(response.json()['articles'][i]['url'])    
strNUS="<br>".join(str(x) for x in listus[0:10])


#uk headlines
url = ('https://newsapi.org/v2/top-headlines?country=gb&'+api_news)
response = requests.get(url)
listGB=[]
for i in range(len(response.json()['articles'])):
    listGB.append(response.json()['articles'][i]['title'])
    listGB.append(response.json()['articles'][i]['url'])
strGB="<br>".join(str(x) for x in listGB[0:10])


#google news(global) headlines
url = ("https://newsapi.org/v2/top-headlines?sources=google-news&"+api_news)
response = requests.get(url)
listg=[]
for i in range(len(response.json()['articles'])):
    listg.append(response.json()['articles'][i]['title'])
    listg.append(response.json()['articles'][i]['url'])
strg="<br>".join(str(x) for x in listg[0:10])


#most popular from technology
url = ("https://newsapi.org/v2/top-headlines?category=technology&country=us&sortBy=popularity&"+api_news)

response = requests.get(url)
listt=[]
for i in range(len(response.json()['articles'])):
    listt.append(response.json()['articles'][i]['title'])
    listt.append(response.json()['articles'][i]['url'])
strt="<br>".join(str(x) for x in listt[0:10])

#yahoo trending charts
page = requests.get("https://finance.yahoo.com/trending-tickers/")
soup = BeautifulSoup(page.content, 'html.parser')
base=soup.findAll('td', {'class':'data-col1 Ta(start) Pstart(10px) Miw(180px)'})
yhoo=[]
for i in base:
    yhoo.append(i.get_text())
strYHOO='<br>'.join(str(x) for x in yhoo[0:15])

#crypto trends to find
with urllib.request.urlopen("https://api.coinmarketcap.com/v2/ticker/") as url:
    cmc = json.loads(url.read().decode())
names=[]
change=[]
for i in cmc['data']:
    names.append(cmc['data'][i]['symbol'])
    change.append(cmc['data'][i]['quotes']['USD']['percent_change_24h'])
change, names = zip(*sorted(zip(change, names)))
cmcstr='<br>'.join([str(a) + ': '+ str(b) + '%' for a,b in zip(names[-5:],change[-5:])])

#create a dict to upload for db
maind={
    "Global Twitter trends": strGT,
    "Polish Twitter trends" : strPLT,
    "Top US headlines": strNUS,
    "Top UK headlines": strGB,
    "Top Google News headlines": strg,
    "Top tech headlines": strt,
    "Trending yahoo stocks": strYHOO,
    "CMC trending": cmcstr,
    "Date": str(datetime.date.today())
}

#create and connect to mongo database
mongo=os.environ["mongodb"]
try: 
    #local test
    #conn = MongoClient()
    #production
    conn = MongoClient(mongo)
    print(conn)
    print("Connected successfully!!!") 
except:   
    print("Could not connect to MongoDB") 
    
#Create/conn database 
db = conn.database 

# Created or Switched to collection names: trends
collection = db.trends

# Insert Data 
rec_id1 = collection.insert_one(maind) 
print("Data inserted with record ids",rec_id1) 

mpass=os.environ["mpass"]

record = collection.find_one({'Date': str(datetime.date.today())}) #create record that is from today
#convert all from database so that its easier to put into mail
gtt=record["Global Twitter trends"]
ptt=record["Polish Twitter trends"]
tus=record["Top US headlines"]
tuk=record["Top UK headlines"]
tgn=record["Top Google News headlines"]
tech=record["Top tech headlines"]
cmc=record["CMC trending"]
yahoo=record["Trending yahoo stocks"]
date=record["Date"]

#crate function to send mail
def send_email(date, *args):
    #login data
    from_email="trendaday21@gmail.com"
    from_password=mpass
    to_email="pokepim@zoho.eu" #recipient

    subject="Daily trends {0}".format(date)
    message="Today's dose of news and trends starting with global twitter trends:<br> <strong>{0}</strong>. <br> <br> Polish twitter:<br> <strong>{1}</strong> <br> <br> Top us headlines:<br> <strong>{2}</strong> <br> <br> Top uk headlines:<br> <strong>{3}</strong> <br> <br> Top news headlines:<br> <strong>{4}</strong> <br> <br> Tech news:<br> <strong>{5}</strong> <br> <br> CMC trending:<br> <strong>{6}</strong> <br> <br> Yahoo trending:<br> <strong>{7}</strong> <br>".format(*args)
    msg=MIMEText(message, 'html') #msg setup
    msg['Subject']=subject
    msg['To']=to_email
    msg['From']=from_email
    gmail=smtplib.SMTP('smtp.gmail.com', 587) #mail setup
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, from_password)
    gmail.send_message(msg)

send_email(date, gtt, ptt, tus, tuk, tgn, tech, cmc, yahoo)