import os
import re
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

TARGET_URL = "https://ustm.jp/ct/kintai/"
ADMIN_ID = "admin7890"

# Step 1 で取得したGASのウェブアプリURLを入力してください
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzNB10avW24GlEiwiQFTlZMF-C1CSWlDoVMu6hYLwuHBbRuxgW3d85tBlF-qdysQgx7/exec"

def run():
    current_ym = datetime.now().strftime("%Y-%m")
    print(f"対象年月: {current_ym}")

    with sync_playwright() as p:
        print("クラウド上のブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # タイムアウト設定
        page.set_default_timeout(30000)

        print("勤怠システムへアクセス中...")
        page.goto(TARGET_URL, wait_until="networkidle")

        print("ログイン処理を実行中...")
        # ID入力欄の取得と入力
        inputs = page.locator("input[type='text'], input[type='password'], input:not([type='hidden'])")
        if inputs.count() > 0:
            inputs.first.fill(ADMIN_ID)
            page.wait_for_timeout(500)
        
        # ログイン・認証ボタンの押下（Enterキー送信含む）
        login_btn = page.locator("button, input[type='submit'], input[type='button']").filter(has_text=re.compile(r"認証|ログイン|送信|決定|次へ"))
        if login_btn.count() > 0 and login_btn.first.is_visible():
            login_btn.first.click()
        else:
            page.keyboard.press("Enter")

        # ログイン後の読み込み待機
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        print(f"期間選択（{current_ym}）を実行中...")
        # 表示されている <select> 要素を探して年月を選択
        selects = page.locator("select")
        for i in range(selects.count()):
            sel = selects.nth(i)
            if sel.is_visible():
                try:
                    sel.select_option(value=current_ym)
                except:
                    try:
                        sel.select_option(label=current_ym)
                    except Exception as e:
                        print(f"選択スキップ: {e}")

        page.wait_for_timeout(1000)

        print("CSVデータ生成・出力処理中...")
        with page.expect_download() as download_info:
            # 画面上の onclick 関数を直接実行して確実にダウンロードを呼び出す
            try:
                page.evaluate("downloadCSV()")
            except Exception as e:
                print("downloadCSV() の直接実行に失敗したためボタンクリックを試行します:", e)
                csv_btn = page.locator("button.csv, button:has-text('CSV'), a:has-text('CSV')").first
                csv_btn.click(force=True)
        
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
