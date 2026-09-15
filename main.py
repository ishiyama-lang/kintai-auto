import os
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://ustm.jp/ct/kintai/"
ADMIN_ID = "admin7890"

# Step 1 で取得したGASのウェブアプリURLをここに貼り付け
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzNB10avW24GlEiwiQFTlZMF-C1CSWlDoVMu6hYLwuHBbRuxgW3d85tBlF-qdysQgx7/exec"

def run():
    with sync_playwright() as p:
        print("クラウド上のブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("勤怠システムへアクセス中...")
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")

        # ログイン処理
        print("ログイン処理を実行中...")
        page.fill("input[type='text'], input[type='password']", ADMIN_ID)
        page.click("button:has-text('認証'), input[type='submit']")
        page.wait_for_timeout(3000)

        # CSVダウンロード実行
        print("CSVデータ生成・出力処理中...")
        with page.expect_download() as download_info:
            page.click("button.csv, button:has-text('CSV出力')")
        
        download = download_info.value
        path = download.path()

        # CSVの中身をテキストとして読み込み
        try:
            with open(path, mode='r', encoding='utf-8-sig') as f:
                csv_text = f.read()
        except:
            with open(path, mode='r', encoding='shift_jis', errors='ignore') as f:
                csv_text = f.read()

        browser.close()

        # GASのURLに向けて、取得したCSVテキストを送信
        print("スプレッドシート（GAS）へデータを送信中...")
        res = requests.post(GAS_WEBAPP_URL, data={'csv_data': csv_text})
        print("送信結果:", res.text)

if __name__ == "__main__":
    run()