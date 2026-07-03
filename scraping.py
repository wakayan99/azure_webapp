# ライブラリのインポート
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import json
import re
import numpy as np
import datetime as dt

# *****************************************
#subscriber, reviewデータの取得とファイル上書き
# *****************************************

# get dummy data from website 
def get_numbers():
    url = 'https://books.toscrape.com/index.html'
    soup = bs(requests.get(url).text, 'html.parser')
    prices = soup.find_all('p', {'class':'price_color'})
    price_list = [float(re.search(r'[\d,]+(?:\.\d+)?', price.text).group().replace(',', '')) for price in prices] 
    n_mean = round(np.mean(price_list), 2)
    n_max = round(np.max(price_list), 2)
    return [n_mean, n_max]


def main():
    #Get data from Google Spread sheet
    with open('secret.json') as f:
        secret = json.load(f)
    GAS_URL = secret['GAS_url']
    response_get = requests.get(GAS_URL)
    data_matrix = response_get.json()  # GASから2次元配列が返ってくる

    if not data_matrix or len(data_matrix) == 0:
        # print("シートが空です。新規のDFを作成します。")
        df = pd.DataFrame(columns=["date", "n_subscriber", "n_review"])
    else:
        # 1行目をヘッダー（列名）、2行目以降をデータとしてDF化
        header = data_matrix[0]
        rows = data_matrix[1:]
        df = pd.DataFrame(rows, columns=header)

    # print("【取得した現在のDataFrame】")
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%dT%H:%M:%S.%fZ" ).dt.strftime('%Y/%m/%d')



    #今日のデータを追加する
    today = dt.date.today().strftime('%Y/%m/%d')
    subscriber, review = get_numbers()
    df.loc[len(df)] = [today, subscriber * 500, review * 60]

    # ====================================================
    # 編集後のDataFrameでスプレッドシートを「上書き」
    # ====================================================
    print("\n--- スプレッドシートの上書きを開始 ---")

    # PandasのDFをGASへ送るために「ヘッダー付きの2次元配列」へ逆変換する
    # DataFrame内の「日付・日時」の列を、すべて文字列に一括変換する
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or df[col].apply(lambda x: isinstance(x, (pd.Timestamp, dt.date))).any():
            df[col] = df[col].astype(str)

    # NaN（欠損値）があるとJSONエラーを起こす可能性があるため、空文字に置換
    df_filled = df.fillna("")

    updated_matrix = [df_filled.columns.tolist()] + df_filled.values.tolist()

    # 送信用パラメータの組み立て
    payload = {
        "matrix": updated_matrix
    }

    # POSTリクエストでGASへデータを送信
    response_post = requests.post(GAS_URL, data=json.dumps(payload))
    # 実行結果の確認
    result = response_post.json()
    if result.get("status") == "success":
        print("スプレッドシートの完全上書きが正常に完了しました！")
    else:
        print(f"エラーが発生しました: {result.get('message')}")


if __name__ == '__main__':
    main()
