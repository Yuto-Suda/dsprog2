import flet as ft
import requests

# APIのエンドポイント
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"

def main(page: ft.Page):
    page.title = "気象庁週間天気予報"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 30
    
    # データを保持する変数
    page.area_data = {}

    # --- UI要素の定義 ---
    center_dd = ft.Dropdown(label="1. 地方を選択", width=250)
    office_dd = ft.Dropdown(label="2. 都道府県を選択", width=250, visible=False)
    result_card = ft.Column(spacing=20)

    # --- 1. 地域リストの初期読み込み ---
    def load_initial_data():
        try:
            res = requests.get(AREA_URL)
            page.area_data = res.json()
            
            options = []
            for code, info in page.area_data["centers"].items():
                options.append(ft.dropdown.Option(key=code, text=info["name"]))
            center_dd.options = options
            page.update()
        except Exception as e:
            print(f"データ読み込みエラー: {e}")

    # --- 2. 地方が選ばれた時の処理 ---
    def on_change_center(e):
        center_code = center_dd.value
        children = page.area_data["centers"][center_code]["children"]
        
        options = []
        for office_code in children:
            name = page.area_data["offices"][office_code]["name"]
            options.append(ft.dropdown.Option(key=office_code, text=name))
        
        office_dd.options = options
        office_dd.visible = True
        office_dd.value = None # 選択をクリア
        result_card.controls.clear()
        page.update()

    # --- 3. 都道府県が選ばれた時の処理（天気取得） ---
    def on_change_office(e):
        office_code = office_dd.value
        if not office_code:
            return

        try:
            res = requests.get(FORECAST_BASE_URL.format(office_code))
            forecast_data = res.json()
            
            # 週間予報データ (index [1])
            weekly_series = forecast_data[1]["timeSeries"]
            times = weekly_series[0]["timeDefines"]
            codes = weekly_series[0]["areas"][0]["weatherCodes"]
            area_name = weekly_series[0]["areas"][0]["area"]["name"]
            
            # 気温データ
            temp_areas = weekly_series[1]["areas"][0]
            mins = temp_areas.get("tempsMin", [])
            maxs = temp_areas.get("tempsMax", [])

            # UIの再構築
            result_card.controls.clear()
            forecast_row = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, spacing=15)

            for i in range(len(times)):
                # 天気コードによる簡易判定
                c = codes[i]
                if c.startswith("1"):
                    icon, color, text = ft.Icons.WB_SUNNY, ft.Colors.ORANGE, "晴れ"
                elif c.startswith("2"):
                    icon, color, text = ft.Icons.CLOUD, ft.Colors.GREY_600, "曇り"
                else:
                    icon, color, text = ft.Icons.UMBRELLA, ft.Colors.BLUE, "雨"

                # 気温（当日分が空文字の場合があるためチェック）
                high = maxs[i] if i < len(maxs) and maxs[i] != "" else "--"
                low = mins[i] if i < len(mins) and mins[i] != "" else "--"

                # カード作成
                forecast_row.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(times[i][5:10].replace("-", "/"), weight="bold"),
                                ft.Icon(name=icon, color=color, size=40),
                                ft.Text(text, size=12),
                                ft.Column([
                                    ft.Text(f"{high}℃", color=ft.Colors.RED, size=18, weight="bold"),
                                    ft.Text(f"{low}℃", color=ft.Colors.BLUE, size=18, weight="bold"),
                                ], spacing=0, horizontal_alignment="center")
                            ], alignment="center", horizontal_alignment="center"),
                            padding=15, width=130
                        )
                    )
                )

            result_card.controls.append(ft.Text(f"【{area_name}】の週間予報", size=24, weight="bold"))
            result_card.controls.append(forecast_row)
            page.update()

        except Exception as err:
            result_card.controls.clear()
            result_card.controls.append(ft.Text(f"取得エラー: {err}", color="red"))
            page.update()

    # イベントの紐付け
    center_dd.on_change = on_change_center
    office_dd.on_change = on_change_office

    # 画面構成
    page.add(
        ft.Column([
            ft.Text("天気予報アプリ", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Row([center_dd, office_dd]),
            ft.Divider(),
            result_card
        ])
    )

    load_initial_data()

ft.app(target=main)