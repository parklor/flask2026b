from flask import Flask, render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from bs4 import BeautifulSoup

# 忽略 SSL 憑證警告
requests.packages.urllib3.disable_warnings()

# 1. 初始化 Firebase (只做一次)
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        print("警告：找不到 Firebase 憑證設定")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# 2. 初始化 Flask (只定義一次)
app = Flask(__name__)

# --- 路由定義區塊 (全部放在 app.run 之前) ---

@app.route("/")
def index():
    homepage = "<h1>羅婉薰Python網頁 20260422</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=wanxun>傳送使用者暱稱</a><br>"
    homepage += "<a href=/account>網頁表單傳值</a><br>"
    homepage += "<a href=/about>婉薰簡介網頁</a><br>"
    homepage += "<a href=/calculator>次方與根號計算</a><br>"
    homepage += "<br><a href=/read2>進入靜宜資管老師查詢系統(互動輸入)</a><br>"
    homepage += "<br><a href=/sp1>爬取子青老師本學期課程</a><br>"
    homepage += "<br><a href=/movie1>爬取即將上映電影</a><br>"
    return homepage

@app.route("/movie1")
def movie1():
    keyword = request.args.get("keyword", "")
    R = f'''<div style="font-family: sans-serif; padding: 20px;">
            <h2>電影查詢系統</h2>
            <form action="/movie1" method="get">
                <input type="text" name="keyword" placeholder="請輸入片名關鍵字" value="{keyword}">
                <button type="submit">搜尋</button>
            </form><hr>'''
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        for item in result:
            a_tag = item.find("a")
            img_tag = item.find("img")
            if a_tag and img_tag:
                movie_name = img_tag.get("alt")
                if keyword.lower() in movie_name.lower():
                    movie_url = "https://www.atmovies.com.tw" + a_tag.get("href")
                    img_src = "https://www.atmovies.com.tw" + img_tag.get("src")
                    R += f'''<div style="margin-bottom: 40px;">
                                <h3>{movie_name}</h3>
                                <a href="{img_src}" target="_blank">
                                    <img src="{img_src}" width="200" style="border: 2px solid #ddd; border-radius: 5px;">
                                </a><br>
                                <p><a href="{movie_url}" target="_blank">🔗 點此查看《{movie_name}》詳細介紹</a></p><hr>
                            </div>'''
    except Exception as e:
        R += f"發生錯誤：{e}"
    R += "</div>"
    return R

@app.route("/sp1")
def spider():
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url, verify=False)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".team-box a")
    R = "<h3>子青老師課程：</h3>"
    for i in result:
        R += f"{i.text} -> {i.get('href')}<br>"
    return R

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/about")
def me():
    return render_template("about.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("nick")
    d = request.values.get("d", "未提供系別")
    c = request.values.get("c", "未提供課程")
    return render_template("welcome.html", name=user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}<br><a href=/>返回首頁</a>"
    return render_template("account.html")

@app.route("/calculator")
def calculator():
    return render_template("calculator.html")

@app.route("/read2")
def read2_input():
    return """<h2>靜宜資管老師查詢系統</h2>
              <form action="/search_result" method="GET">
                  <p>關鍵字：<input type="text" name="keyword"><button type="submit">查詢</button></p>
              </form><br><a href="/">返回首頁</a>"""

@app.route("/search_result")
def search_result():
    keyword = request.values.get("keyword", "").strip()
    db = firestore.client()
    docs = db.collection("靜宜資管").get()
    res = f"<h3>「{keyword}」的搜尋結果：</h3><table border=1>"
    count = 0
    for doc in docs:
        t = doc.to_dict()
        if keyword in t.get("name", ""):
            count += 1
            res += f"<tr><td>{t.get('name')}</td><td>{t}</td></tr>"
    res += "</table>"
    return res + f"<p>共 {count} 筆</p><a href='/'>首頁</a>"

# 3. 最後才執行 app.run
if __name__ == "__main__":
    app.run(debug=True, port=5000)