# ライブラリのインポート
from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
import numpy as np
import datetime as dt
import streamlit as st
import os
import altair as alt

def get_ec_data():
    data = []
    url_ec = 'https://webscraper.io/test-sites/e-commerce/allinone'
    res = requests.get(url_ec)
    item_list = bs(res.text, 'html.parser').find_all('div', {'class':'product-wrapper card-body'})
    item_data = []
    for item in item_list:
        item_info = {}
        item_info['item_name'] = item.find('p', {'class':'description card-text'}).text
        item_price = item.find('span', {'itemprop':'price'}).text
        item_info['item_price(EUR)'] = int(re.search(r'[\d,]+', item_price).group().replace(",", ""))
        item_info['item_link'] = item.find('a')['href']
        item_info['is_reviewed'] = 'レビューあり' if int(item.find('span', {'itemprop':'reviewCount'}).text) > 0 else 'レビューなし'
        item_data.append(item_info)
    
    return pd.DataFrame(item_data)

def get_spreadsheet():
    #Get data from Google Spread sheet
    GAS_URL = os.getenv('GAS_url')
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
    df['date'] = pd.to_datetime(df['date'],
                 format="%Y-%m-%dT%H:%M:%S.%fZ" ).dt.strftime('%Y/%m/%d')
    
    return df

def draw_chart():
    ### get spread sheet data
    ss_data = get_spreadsheet()
    sub_min, sub_max = ss_data['n_subscriber'].min()-10, ss_data['n_subscriber'].max()+10
    rev_min, rev_max = ss_data['n_review'].min()-10, ss_data['n_review'].max()+10

    ###draw chart
    base = alt.Chart(ss_data).encode(alt.X('date:T', axis = alt.Axis(title = None)))

    line1 = base.mark_line(opacity = 0.3, color = '#57A44C').encode(
        alt.Y('n_subscriber', axis = alt.Axis(title = '受講者数', titleColor = '#57A44C'),
            scale = alt.Scale(domain = [sub_min, sub_max])
        ))

    line2 = base.mark_line(stroke = '#5276A7', interpolate = 'monotone').encode(
        alt.Y('n_review',
            axis = alt.Axis(title = 'レビュー数', titleColor = '#5276A7'),
            scale = alt.Scale(domain = [rev_min, rev_max])
    ))

    chart = alt.layer(line1, line2).resolve_scale(
        y = 'independent'
    )

    return chart


chart = draw_chart()
df_ec = get_ec_data()

st.title('webスクレイピング活用アプリ')

st.write('## Udemy 情報')
st.altair_chart(chart, use_container_width=True)

st.write('## EC 在庫情報', df_ec)

