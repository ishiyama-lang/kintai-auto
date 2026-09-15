import os
import requests
from playwright.sync_api import sync_playwright

TARGET_URL = "https://ustm.jp/ct/kintai/"
ADMIN_ID = "admin7890"

# Step 1 で取得したGASのウェブアプリURLを入力してください
GAS_WEBAPP_URL = "ここにGASのウェブアプリURLを貼り付け"

def run():
    with sync_playwright() as p:
        print("クラウド上のブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        # 画面サイズを広めに設定して要素の非表示を防ぐ
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # タイムアウトを60秒に延長
        page.set_default_timeout(60000)

        print("勤怠システムへアクセス中...")
        page.goto(TARGET_URL, wait_until="networkidle")

        print("ログイン処理を実行中...")
        # 入力欄の探索（テキストボックスを探して入力）
        inputs = page.locator("input[type='text'], input[type='password'], input:not([type='hidden'])")
        if inputs.count() > 0:
            inputs.first.fill(ADMIN_ID)
        
        # 認証・ログインボタンの判定とクリック
        login_btn = page.locator("button, input[type='submit'], input[type='button']").filter(has_text=lambda t: any(k in t for k in ["認証", "ログイン", "送信", "決定"]))
        if login_btn.count() > 0:
            login_btn.first.click()
        else:
            page.keyboard.press("Enter")
        
        page.wait_for_timeout(5000)

        print("CSVデータ生成・出力処理中...")
        # CSV出力ボタンの探索とクリック
        csv_btn = page.locator("button, a, input").filter(has_text=lambda t: any(k in t for k in ["CSV", "出力", "ダウンロード", "エクスポート"]))
        
        with page.expect_download() as download_info:
            if csv_btn.count() > 0:
                csv_btn.first.click()
            else:
                raise Exception("CSV出力ボタンが見つかりませんでした。")
        
        download = download_info.value
        path = download.path()

        # CSVの中身を読み込み
        try:
            with open(path, mode='r', encoding='utf-8-sig') as f:
                csv_text = f.read()
        except:
            with open(path, mode='r', encoding='shift_jis', errors='ignore') as f:
                csv_text = f.read()

        browser.close()

        print("スプレッドシート（GAS）へデータを送信中...")
        res = requests.post(GAS_WEBAPP_URL, data={'csv_data': csv_text})
        print("送信結果:", res.text)

if __name__ == "__main__":
    run()
