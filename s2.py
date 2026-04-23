import requests
from bs4 import BeautifulSoup

url ="https://flask2026b-sepia.vercel.app/about"
Data = requests.get(url)
Data.encoding="utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.find("a")
#print(result)
for item in result:
	print(item.text)
	print()
