# from flask import Flask, render_template, jsonify
# import psycopg2
# import psycopg2.extras
#
# # DB 설정 (infomax.py와 동일하게 유지)
# DB_CONFIG = {
#     "host": "localhost",
#     "port": 5432,
#     "dbname": "els_db",
#     "user": "els",
#     "password": "long123!!!",
# }
#
# # Flask 앱 생성 (현재 폴더의 html을 템플릿으로 사용)
# app = Flask(__name__, template_folder=".")
#
# def get_dashboard_meta():
#     """
#     timeseries_strategy 테이블에서 대시보드에 필요한 데이터 한 번에 가져오기:
#       - 가장 최근 Position / 이전 Position
#       - 가장 최근 P_진입 (진입 가격)
#       - 최근 100개 일자 / 종가 / 예측 시계열
#     """
#     conn = psycopg2.connect(**DB_CONFIG)
#     try:
#         with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
#             # 1) 가장 최근 2개 행: Position + P_진입
#             cur.execute("""
#                 SELECT "일자", "Position", "P_진입"
#                 FROM macd
#                 ORDER BY "일자" DESC
#                 LIMIT 2
#             """)
#             rows_pos = cur.fetchall()
#
#             last_position = rows_pos[0]["Position"] if len(rows_pos) >= 1 else None
#             previous_position = rows_pos[1]["Position"] if len(rows_pos) >= 2 else None
#             entry_price = rows_pos[0]["P_진입"] if len(rows_pos) >= 1 else None
#
#             # 2) 최근 100개: 일자 / 종가 / 예측
#             cur.execute("""
#                 SELECT "일자", "종가", "MA_5"
#                 FROM macd
#                 ORDER BY "일자" DESC
#                 LIMIT 100
#             """)
#             rows_chart = cur.fetchall()
#
#             # DESC로 가져왔으니, 그래프는 시간 순으로 보이도록 역순 정렬
#             rows_chart = list(reversed(rows_chart))
#
#             labels = []
#             actual_close_series = []
#             trend_series = []
#
#             for r in rows_chart:
#                 d = r["일자"]
#                 # 날짜 포맷 정리 (원하는 포맷으로 변경 가능)
#                 if hasattr(d, "strftime"):
#                     label = d.strftime("%Y-%m-%d")
#                 else:
#                     label = str(d)
#
#                 labels.append(label)
#                 actual_close_series.append(float(r["종가"]) if r["종가"] is not None else None)
#                 trend_series.append(float(r["MA_5"]) if r["MA_5"] is not None else None)
#
#             return {
#                 "last_position": last_position,
#                 "previous_position": previous_position,
#                 "entry_price": entry_price,
#                 "workday_labels": labels,
#                 "actual_close_series": actual_close_series,
#                 "trend_series": trend_series,
#             }
#     finally:
#         conn.close()
#
# # 1) 메인 페이지: HTML 렌더링
# @app.route("/")
# def index():
#     # cnn_longshort_dashboard_v4.html 파일이 dash.py와 같은 폴더에 있어야 함
#     return render_template("cnn_longshort_dashboard_v4.html")
#
# # 2) 대시보드 메타데이터 API
# @app.route("/api/last-position")
# def api_last_position():
#     meta = get_dashboard_meta()
#     return jsonify(meta)
#
# # 3) 서버 실행
# if __name__ == "__main__":
#     app.run(debug=True)










###-------------------------------------------------------------------------------------------------------------------###
from flask import Flask, render_template, jsonify
import psycopg2
import psycopg2.extras

# DB 설정
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "els_db",
    "user": "els",
    "password": "long123!!!",
}

app = Flask(__name__, template_folder=".")

# ─────────────────────────────────────────────
#  전략별 테이블 / 컬럼 설정
#  ※ 실제 컬럼명에 맞게 trend_col 은 수정해서 사용하세요.
# ─────────────────────────────────────────────
STRATEGY_CONFIG = {
    "rsi": {
        "table": "rsi",        # 예: rsi 테이블
        "trend_col": "%K_final",  # 예: RSI 기반 추세 컬럼명 (실제 이름으로 수정)
    },
    "macd": {
        "table": "macd",
        "trend_col": "MA_5",   # 질문에 주신 예시 그대로 사용
    },
    "tf": {
        "table": "tf",         # 예: tf 테이블
        "trend_col": "P_SLOPE",   # 예: TF 전략 추세 컬럼명 (실제 이름으로 수정)
    },
}


def get_dashboard_meta(strategy_key: str):
    """
    공통 대시보드 메타 조회 함수
    - 전략 종류(rsi / macd / tf)에 따라 테이블, 추세 컬럼만 바꿔서 동일 로직 실행
    """
    if strategy_key not in STRATEGY_CONFIG:
        raise ValueError(f"지원하지 않는 전략: {strategy_key}")

    cfg = STRATEGY_CONFIG[strategy_key]
    table = cfg["table"]
    trend_col = cfg["trend_col"]

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1) 가장 최근 2개 행: Position + P_진입
            cur.execute(f"""
                SELECT "일자", "Position", "P_진입"
                FROM {table}
                ORDER BY "일자" DESC
                LIMIT 2
            """)
            rows_pos = cur.fetchall()

            last_position = rows_pos[0]["Position"] if len(rows_pos) >= 1 else None
            previous_position = rows_pos[1]["Position"] if len(rows_pos) >= 2 else None
            entry_price = rows_pos[0]["P_진입"] if len(rows_pos) >= 1 else None

            # 2) 최근 100개: 일자 / 종가 / 추세(전략별 컬럼)
            cur.execute(f"""
                SELECT "일자", "종가", "{trend_col}"
                FROM {table}
                ORDER BY "일자" DESC
                LIMIT 100
            """)
            rows_chart = cur.fetchall()

            # DESC로 가져왔으니 시간 순서로 뒤집기
            rows_chart = list(reversed(rows_chart))

            labels = []
            actual_close_series = []
            trend_series = []

            for r in rows_chart:
                d = r["일자"]
                if hasattr(d, "strftime"):
                    label = d.strftime("%Y-%m-%d")
                else:
                    label = str(d)

                labels.append(label)
                actual_close_series.append(
                    float(r["종가"]) if r["종가"] is not None else None
                )
                trend_series.append(
                    float(r[trend_col]) if r[trend_col] is not None else None
                )

            return {
                "strategy": strategy_key,
                "last_position": last_position,
                "previous_position": previous_position,
                "entry_price": entry_price,
                "workday_labels": labels,
                "actual_close_series": actual_close_series,
                "trend_series": trend_series,
            }
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  1) 메인 페이지
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("cnn_longshort_dashboard_v4.html")


# ─────────────────────────────────────────────
#  2) 전략별 메타데이터 API
#     - 프론트에서 각 탭 전환 시 이 URL만 다르게 호출하면 됨
# ─────────────────────────────────────────────
@app.route("/api/strategy/<strategy_key>")
def api_strategy(strategy_key):
    strategy_key = strategy_key.lower()
    if strategy_key not in STRATEGY_CONFIG:
        return jsonify({"error": f"unknown strategy: {strategy_key}"}), 400

    meta = get_dashboard_meta(strategy_key)
    return jsonify(meta)


# ─────────────────────────────────────────────
#  3) 기존 RSI용 엔드포인트 호환 유지
#     - 현재 JS에서 /api/last-position 을 쓰고 있다면 그대로 사용 가능
# ─────────────────────────────────────────────
@app.route("/api/last-position")
def api_last_position():
    # 기존 코드와의 호환을 위해 RSI 전략을 default 로 사용
    meta = get_dashboard_meta("rsi")
    return jsonify(meta)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",   # 전체 인터페이스에서 접속 허용
        port=5000,
        debug=True
    )
