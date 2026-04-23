from flask import Flask, render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from bs4 import BeautifulSoup

# 忽略 SSL 憑證警告（針對學校網站）
requests.packages.urllib3.disable_warnings()

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)
app = Flask(__name__)

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

app = Flask(__name__)

@app.route("/movie1")
def movie1():
    keyword = request.args.get("keyword", "")
    
    R = f'''
        <div style="font-family: sans-serif; padding: 20px;">
            <h2>電影查詢系統</h2>
            <form action="/movie1" method="get">
                <input type="text" name="keyword" placeholder="請輸入片名關鍵字" value="{keyword}">
                <button type="submit">搜尋</button>
            </form>
            <hr>
    '''
    
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
                    
                    R += f'''
                        <div style="margin-bottom: 40px;">
                            <h3>{movie_name}</h3>
                            
                            <a href="{img_src}" target="_blank">
                                <img src="{img_src}" width="200" title="點擊看大圖" style="border: 2px solid #ddd; border-radius: 5px;">
                            </a>
                            
                            <br>
                            
                            <p>
                                <a href="{movie_url}" target="_blank" style="text-decoration: none; color: #E44D26; font-weight: bold;">
                                    🔗 點此查看《{movie_name}》詳細介紹
                                </a>
                            </p>
                            <hr>
                        </div>
                    '''
    except Exception as e:
        R += f"發生錯誤：{e}"

    R += "</div>"
    return R

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/sp1")
def spider():
        R = ""
        url = "https://www1.pu.edu.tw/~tcyang/course.html"
        Data = requests.get(url, verify=False)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".team-box a")

        for i in result:
            R += i.text+i.get("href")+"<br>"
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
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}<br><a href=/>返回首頁</a>"
    else:
        return render_template("account.html")

@app.route("/calculator")
def calculator():
    return render_template("calculator.html")

@app.route("/read")
def read_all():
    Result = "<h3>全部老師資料清單</h3>"
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get()    
    for doc in docs:          
        Result += str(doc.to_dict()) + "<br><br>"    
    return Result + "<a href=/>返回首頁</a>"

@app.route("/read2")
def read2_input():
    html = """
    <h2>靜宜資管老師查詢系統</h2>
    <form action="/search_result" method="GET">
        <p>請輸入要搜尋的老師姓名關鍵字：
        <input type="text" name="keyword" placeholder="例如：王">
        <button type="submit">開始查詢</button></p>
    </form>
    <br><a href="/">返回首頁</a>
    """
    return html

@app.route("/search_result")
def search_result():
    keyword = request.values.get("keyword", "").strip()
    if not keyword:
        return "您沒有輸入關鍵字！<br><a href='/read2'>重新查詢</a>"

    db = firestore.client()
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.get()

    found_count = 0
    table_html = f"""
    <h3>關於「{keyword}」的搜尋結果：</h3>
    <style>
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #2196f3; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
    <table>
        <tr>
            <th>老師姓名</th>
            <th>詳細資料</th>
        </tr>
    """

    for doc in docs:
        teacher = doc.to_dict()
        if keyword in teacher.get("name", ""):
            found_count += 1
            table_html += f"<tr><td><strong>{teacher.get('name')}</strong></td><td>{str(teacher)}</td></tr>"

    table_html += "</table>"

    if found_count == 0:
        return f"查無姓名包含「{keyword}」的老師資料。<br><a href='/read2'>重新查詢</a>"

    return table_html + f"<br><p>共找到 {found_count} 筆資料</p><a href='/'>返回首頁</a>"

if __name__ == "__main__":
    app.run(debug=True)