import streamlit as st
import pandas as pd
import numpy as np
import re

# サイドバーでページを選択
page = st.sidebar.selectbox("ページ選択", ["ランキング", "選手リスト管理", "成績入力", "順位と得点の換算定義"])

# デフォルトの得点定義
def init_point_definition():
    if "edited_data" in st.session_state:
        st.session_state["edited_data"].clear()

    st.session_state["default_point_definition"] = {
        "takamatsunomiya":{
            "title_jp":"高松宮記念杯競輪",
            "points":{
                "first_round":[10,9,8,7,6,5,4,3,2,1,0,0],
                "second_round":[13,11,9,7,6,5,4,3,2,1,0,0],
            },
            "caution":0
        },
        "all_star":{
            "title_jp":"オールスター競輪",
            "points":{
                "first_round":[10,9,8,7,6,5,4,3,2,1,0,0],
                "second_round":[13,11,10,9,8,7,6,5,4,1,0,0],
                "dream":[18,17,16,15,14,13,12,11,10,8,0,0],
                "orion":[15,14,13,12,11,10,9,8,7,5,0,0],
            },
        },
        "keirinsai":{
            "title_jp":"競輪祭",
            "points":{
                "first_round":[10,9,8,7,6,5,4,3,2,1,0,0],
                "second_round":[13,11,9,7,6,5,4,3,2,1,0,0],
            },
        },
    }

    # 編集用のデータを用意する
    st.session_state["point_definition"] = st.session_state["default_point_definition"]

    # デフォルト３レースの定義を保持する
    for race in st.session_state["point_definition"]:
        if f"df_ptdef_{race}" in st.session_state:
            del st.session_state[f"df_ptdef_{race}"]
        st.session_state[f"df_ptdef_{race}"] = pd.DataFrame(
            data=st.session_state["point_definition"][race]["points"],
            index=["1着","2着","3着","4着","5着","6着","7着","8着","9着","棄","失","欠"],
    )


# 共有データフレームの初期化
# 選手データの初期化
def init_players():
    st.session_state["df_scores"] = pd.DataFrame({
        "player_id": pd.Series(dtype="str"),
        "player_name": pd.Series(dtype="str"),
        "election_rank": pd.Series(dtype="int"),
        "first_round": pd.Series(dtype="int"),
        "second_round": pd.Series(dtype="int"),
    })
    st.session_state["input_players"] = pd.DataFrame(
        data=[["" for x in range(2)] for y in range(200)],
        columns=["player_name","player_id"],
        dtype="str"
    )

# フラグの初期化
def init_flags():
    st.session_state["flags"] = True
    st.session_state["up_pl_btn"] = True
    st.session_state["up_sc_btn"] = True
    st.session_state["dl_pl_btn"] = True

# 選択中レースの初期化
def init_active_race():
    st.session_state["active_race"] = "takamatsunomiya"
    st.session_state["active_race_index"] = 0

# 成績更新用の初期化
def init_input_scores():
    st.session_state["input_scores"] = pd.DataFrame([[None for x in range(4)] for y in range(9)])
    st.session_state["new_scores"] = pd.DataFrame([[None for x in range(4)] for y in range(9)])

# 選択レースの更新
def update_active_race():
    st.session_state["active_race_index"] \
    = list(st.session_state["point_definition"]).index([x for x in st.session_state["point_definition"] \
    if st.session_state["point_definition"][x]["title_jp"] == st.session_state["new_active_race"]][0])
    st.session_state["active_race"] = list(st.session_state["point_definition"])[st.session_state["active_race_index"]]

# 得点定義の更新
def update_point_definition():
    for index in list(st.session_state["edited_data"]["edited_rows"].keys()):
        for column, value in list(st.session_state["edited_data"]["edited_rows"][index].items()):
            st.session_state[f"""df_ptdef_{st.session_state["active_race"]}"""].iloc[int(index),st.session_state[f"""df_ptdef_{st.session_state["active_race"]}"""].columns.get_loc(column)] = value

# csvファイルの存在有無でのボタン用フラグ制御
def check_file():
    if st.session_state["upfile"] is not None:
        st.session_state["up_pl_btn"] = True
    else:
        st.session_state["up_pl_btn"] = False

# コピペエリアの存在有無でのボタン用フラグ制御
def check_data():
    if input_area is not None:
        st.session_state["up_sc_btn"] = False
    else:
        st.session_state["up_sc_btn"] = True

# 選手情報更新
# アップロードされた選手リストCSVを読み込んで選手リスト更新を行う
def update_players():
    try:
        temp_df = pd.read_csv(
            st.session_state["upfile"],
            dtype={
                "player_id":"str",
                "player_name":"str",
                "first_round":"int",
                "second_round":"int",
                "election_rank":"int"
                }
            )
        if "player_id" in temp_df.columns and temp_df.columns.size >= 1:
            st.session_state["df_scores"]["player_id"] = temp_df["player_id"]
            st.session_state["df_scores"]["player_name"] = temp_df["player_name"]
            st.session_state["df_scores"]["first_round"] = temp_df["first_round"]
            st.session_state["df_scores"]["second_round"] = temp_df["second_round"]
            st.session_state["df_scores"]["election_rank"] = temp_df["election_rank"]
            st.session_state["df_scores"] = st.session_state["df_scores"].fillna({
                "player_name":"",
                "first_round":0,
                "second_round":0,
                "election_rank":0,
                }).astype({
                "first_round":"int64",
                "second_round":"int64",
                "election_rank":"int64",
            })
            st.toast("選手リストを読み込みました。",icon="👍")
    except:
        st.toast("更新失敗！CSVファイルの形式が正しくありません。最低でもplayer_idの列が必要です。",icon="👎")
    finally:
        st.session_state["upfile"] is None
        init_flags()

# 成績更新
def update_scores():
    try:
        st.session_state["new_scores"] = input_area
        for index, row in st.session_state["new_scores"].iterrows():
            if row["0"] == None:
                continue
            chaku = row["0"]
            _player_id = re.match(r"https://keirin.netkeiba.com/db/profile/\?id=(\d+|[a-z]+)",row["3"]).group(1)
            if st.session_state["pattern"] == "dream" or st.session_state["pattern"] == "orion":
                st.session_state["df_scores"].loc[st.session_state["df_scores"]["player_id"] == str(_player_id),"first_round"] \
                = st.session_state[f"""df_ptdef_{st.session_state["active_race"]}"""].loc[chaku,st.session_state["pattern"]]
            else:
                st.session_state["df_scores"].loc[st.session_state["df_scores"]["player_id"] == str(_player_id),st.session_state["pattern"]] \
                = st.session_state[f"""df_ptdef_{st.session_state["active_race"]}"""].loc[chaku,st.session_state["pattern"]]
        st.toast("レース成績を読み込みました。",icon="👍")
    except:
        st.toast("レース成績読み込み失敗！コピペ失敗してるかも",icon="👎")
    finally:
        init_input_scores()

# 選手IDと選手名の更新
def update_plist():
    st.session_state["input_players"] = input_players
    st.session_state["input_players"].replace(r"https://keirin.netkeiba.com/db/profile/\?id=(\d+|[a-z]+)",r"\1",inplace=True,regex=True)
    st.session_state["dl_pl_btn"] = False

# 入力エリアから選手リストへ情報更新
def convert_plist():
    st.session_state["df_scores"]["player_id"] = st.session_state["input_players"]["player_id"]
    st.session_state["df_scores"]["player_name"] = st.session_state["input_players"]["player_name"]
    st.session_state["df_scores"] = st.session_state["df_scores"].fillna({
        "player_name":"",
        "first_round":0,
        "second_round":0,
        "election_rank":0,
    }).astype({
        "player_id":"str",
        "player_name":"str",
        "first_round":"int64",
        "second_round":"int64",
        "election_rank":"int64",
    })
    # 重複行を消す
    st.session_state["df_scores"] = st.session_state["df_scores"].drop_duplicates()
    # 選手IDがないデータはランキングに不要なので消す
    st.session_state["df_scores"] = st.session_state["df_scores"][st.session_state["df_scores"]["player_id"] != ""]

# 初期化実行
if "df_scores" not in st.session_state:
    init_players()

if "default_point_definition" not in st.session_state:
    init_point_definition()

if "active_race" not in st.session_state:
    init_active_race()

if "flags" not in st.session_state:
    init_flags()

if "input_scores" not in st.session_state:
    init_input_scores()

# ページごとの処理
if page == "ランキング":
    # ランキング表示と最新ランキングデータをダウンロードできる
    st.title(f"""{st.session_state["point_definition"][st.session_state["active_race"]]["title_jp"]} ランキング""")

    # ダウンロード用CSVの設定
    csv = st.session_state["df_scores"].to_csv(columns=["player_id","player_name","election_rank","first_round","second_round"],index=False).encode("utf-8")
    st.download_button(
        label="選手リストをダウンロードする",
        data=csv,
        file_name=f"""{st.session_state["point_definition"][st.session_state["active_race"]]["title_jp"]} ランキング.csv""",
        mime="text/csv",
        key="dl_csv"
    )
    st.session_state["df_scores"]["total_score"] = st.session_state["df_scores"]["first_round"] + st.session_state["df_scores"]["second_round"]
    st.session_state["df_scores"]["image"] = st.session_state["df_scores"]["player_id"].map(lambda x:f"https://cdn.netkeiba.com/keirin/common/img/players/player_{x}.jpg")
    rankings = st.session_state["df_scores"].sort_values(by=["total_score","election_rank"],ascending=[False,True],ignore_index=True)
    rankings["rank"] = [f"""{int(x)+1}位""" for x in rankings.reset_index().index.tolist()]
    st.dataframe(
        data=rankings[["rank","image","player_name", "first_round", "second_round", "total_score"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "rank":st.column_config.TextColumn("順位"),
            "image":st.column_config.ImageColumn(
                "写真",
                help="選手の顔写真"
                ),
            "player_name":st.column_config.TextColumn("選手名"),
            "first_round":st.column_config.TextColumn("1走目"),
            "second_round":st.column_config.TextColumn("2走目"),
            "total_score":st.column_config.TextColumn("合計pt"),
            }
        )
    # ニュース用にそのままコピペする用の表
    news_ranking = rankings.rename(
        columns={
            "rank":"順位",
            "player_name":"選手名",
            "election_rank":"選考順位",
            "total_score":"合計pt",
            },
        )
    news_ranking["結果"] = ""
    st.divider()
    st.header("ニュース用")
    tsv = news_ranking.to_csv(columns=["順位","選手名", "選考順位", "合計pt","結果"],index=False,sep="\t").encode("utf-8")
    # st.button(
    #     label="ニュース用にコピーする",
    #     key="cp_df",
    #     on_click=news_ranking.to_clipboard(columns=["順位","選手名", "選考順位", "合計pt","結果"],index=False)
    # )
    st.dataframe(
        data=news_ranking[["順位","選手名", "選考順位", "合計pt","結果"]],
        hide_index=True,
        use_container_width=True
    )
    

elif page == "選手リスト管理":
    st.title("選手リスト管理")
    st.header("選手リストの初期化")
    init_button = st.button("選手リストを初期化する",on_click=init_players,type="primary")
    st.divider()
    st.header("選手リストの登録")
    st.session_state["upfile"] = st.file_uploader("選手リストをアップロードしてください（CSV形式）", type="csv",on_change=check_file)
    update_button = st.button("選手リストを更新する",on_click=update_players,disabled=st.session_state.get("up_pl_btn",True))
    st.divider()
    st.header("選手IDをコピペで取る用")
    input_players = st.data_editor(
        data=st.session_state["input_players"],
        key="eee_players",
        num_rows="fixed",
    )
    st.button("選手IDを更新する",on_click=update_plist,key="aaa")
    st.button(
        label="選手リストを更新する",
        on_click=convert_plist,
        type="primary",
        disabled=st.session_state.get("dl_pl_btn",True),
        key="cvt"
    )

elif page == "成績入力":
    st.title("成績入力")
    round_option = st.selectbox(
        label="レース種別選択", 
        options=st.session_state["point_definition"][st.session_state["active_race"]]["points"],
        key="pattern"
    )
    input_area = st.data_editor(
        data=st.session_state["input_scores"],
        key="result",
        num_rows="fixed",
    )
    update_scores_button = st.button("成績を更新する", on_click=update_scores)


elif page == "順位と得点の換算定義":
    st.title("順位と得点の換算定義")
    st.write("順位ごとの得点ルールをここで設定できます。")

    st.selectbox(
        label="レースを選択する",
        options=[st.session_state["point_definition"][x]["title_jp"] for x in st.session_state["point_definition"]],
        key="new_active_race",
        index=st.session_state["active_race_index"],
        placeholder="レースを選択してください",
        on_change=update_active_race,
    )
    st.divider()
    st.data_editor(
        data=st.session_state[f"""df_ptdef_{st.session_state["active_race"]}"""],
        key="edited_data",
        num_rows="fixed",
        on_change=update_point_definition
        )
    st.button("定義を初期化する",on_click=init_point_definition,type="primary")
