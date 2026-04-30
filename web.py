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
cred = None
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        print("警告：找不到 Firebase 憑證設定")

if cred and not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# 2. 初始化 Flask
app = Flask(__name__)

# --- 路由定義區塊 ---

@app.route("/")
def index():
    homepage = "<h1>羅婉薰Python網頁 20260422</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=wanxun>傳送使用者暱稱</a><br>"
    homepage += "<a href=/account>網頁表單傳值</a><br>"
    homepage += "<a href=/about>婉薰簡介網頁</a><br>"
    homepage += "<a href=/calculator>次方與根號計算</a><br>"
    homepage += "<br><a href=/read2>進入靜宜資管老師查詢系統</a><br>"
    homepage += "<br><a href=/sp1>爬取子青老師本學期課程</a><br>"
    homepage += "<br><a href=/movie1>線上爬取電影</a><br>"
    homepage += "<br><a href=/spidermovie>電影資料庫(爬取、更新與查詢)</a><br>"
    return homepage

@app.route("/spidermovie", methods=["GET", "POST"])
def spidermovie():
    db = firestore.client()
    keyword = request.values.get("keyword", "").strip()
    action = request.values.get("action", "")
    
    message = ""
    
    # --- 功能：爬取並存入資料庫 ---
    if action == "update":
        url = "http://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        
        try:
            lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：", "")
        except:
            lastUpdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = sp.select(".filmListAllX li")
        total = 0 

        for item in result:
            try:
                total += 1
                movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
                title = item.find(class_="filmtitle").text.strip()
                picture = "https://www.atmovies.com.tw" + item.find("img").get("src")
                hyperlink = "https://www.atmovies.com.tw" + item.find("a").get("href")
                
                runtime_tag = item.find(class_="runtime")
                showDate = runtime_tag.text[5:15] if runtime_tag else "未知"
                
                doc = {
                    "title": title,
                    "picture": picture,
                    "hyperlink": hyperlink,
                    "showDate": showDate,
                    "lastUpdate": lastUpdate
                }
                db.collection("電影2B").document(movie_id).set(doc)
            except:
                continue
        message = f'''<div style="background-color: #d4edda; padding: 10px; border-radius: 5px; color: #155724;">
                        ✅ 更新成功！最近更新日期：{lastUpdate}，共爬取 {total} 部電影。
                      </div>'''

    # --- 建立 UI 介面 ---
    R = f'''<div style="font-family: sans-serif; padding: 20px;">
            <h2>電影資料庫管理系統</h2>
            
            <div style="margin-bottom: 20px;">
                <form action="/spidermovie" method="post" style="display: inline-block; margin-right: 10px;">
                    <input type="hidden" name="action" value="update">
                    <button type="submit" style="background-color: #007bff; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer;">
                        🔄 爬取即將上映電影並更新資料庫
                    </button>
                </form>
            </div>
            
            {message}
            
            <hr>
            <h3>資料庫查詢</h3>
            <form action="/spidermovie" method="get">
                <input type="text" name="keyword" placeholder="請輸入片名關鍵字" value="{keyword}">
                <button type="submit">從資料庫查詢</button>
            </form>
            <br>'''

    # --- 功能：查詢資料庫 ---
    docs = db.collection("電影2B").get()
    res_table = '<table border="1" style="border-collapse: collapse; width: 100%; text-align: center;">'
    res_table += '<tr style="background-color: #f2f2f2;"><th>編號</th><th>片名</th><th>海報</th><th>介紹頁</th><th>上映日期</th></tr>'
    
    count = 0
    for doc in docs:
        movie_data = doc.to_dict()
        title = movie_data.get("title", "")
        if keyword.lower() in title.lower():
            count += 1
            res_table += f'''<tr>
                            <td>{doc.id}</td>
                            <td>{title}</td>
                            <td><img src="{movie_data.get("picture")}" width="100"></td>
                            <td><a href="{movie_data.get("hyperlink")}" target="_blank">點此查看</a></td>
                            <td>{movie_data.get("showDate")}</td>
                          </tr>'''
    res_table += "</table>"
    
    if count > 0:
        R += f"<p>查詢結果：找到 {count} 筆符合的資料。</p>" + res_table
    elif keyword != "":
        R += f"<p>找不到包含「{keyword}」的電影資料。</p>"

    R += "<br><a href=/>返回首頁</a></div>"
    return R

# --- 其他功能保持不變 ---
@app.route("/movie1")
def movie1():
    keyword = request.args.get("keyword", "")
    R = f'''<div style="font-family: sans-serif; padding: 20px;">
            <h2>電影即時爬取系統 (不存資料庫)</h2>
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
    R += "<br><a href=/>返回首頁</a></div>"
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
    R += "<br><a href=/>返回首頁</a>"
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)