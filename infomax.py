import os
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine

# ======================================
#  DB 설정
# ======================================
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'els_db'),
    'user': os.getenv('DB_USER', 'els'),
    'password': os.getenv('DB_PASSWORD', 'long123!!!')
}

# ======================================
#  DB 연결 문자열
# ======================================
def build_connection_string(config: dict) -> str:
    user = quote_plus(config["user"])
    password = quote_plus(config["password"])
    host = config["host"]
    port = config["port"]
    database = config["database"]
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

# ======================================
#  업로드 함수
# ======================================
def update_dataframe_to_sql(df, table_name, db_config, if_exists='replace'):
    if df.empty:
        print(f"⚠️ 시트 내용이 비어 있어 업로드 생략됨 → {table_name}")
        return False

    connection_string = build_connection_string(db_config)

    try:
        engine = create_engine(connection_string)
        print(f"\n📌 SQL 테이블 '{table_name}' 업데이트 시작")
        print(f"   - 행 수: {len(df)}")
        print(f"   - 컬럼 수: {len(df.columns)}")

        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )

        print(f"✅ '{table_name}' 업데이트 완료!")
        return True

    except Exception as e:
        print(f"❌ SQL 업데이트 오류 ({table_name}): {e}")
        return False

    finally:
        if 'engine' in locals():
            engine.dispose()

# ======================================
#  strategy_fund.xlsx → 3개 테이블 생성
# ======================================
if __name__ == "__main__":

    excel_file = "strategy_fund.xlsx"

    # 시트 인덱스 → SQL 테이블명
    sheet_to_table = {0: "rsi",
                      1: "macd",
                      2: "tf"}

    for sheet_idx, table_name in sheet_to_table.items():

        print(f"\n==============================")
        print(f"📄 엑셀 시트 {sheet_idx} → SQL 테이블 '{table_name}'")
        print(f"==============================")

        try:
            # ⚠️ 반드시 header=4 유지 (5번째 줄부터 실제 데이터)
            df = pd.read_excel(excel_file, sheet_name=sheet_idx, header=3)
        except Exception as e:
            print(f"❌ 엑셀 시트 읽기 실패 ({sheet_idx}): {e}")
            continue

        update_dataframe_to_sql(
            df=df,
            table_name=table_name,
            db_config=db_config,
            if_exists='replace'
        )

    print("\n🎉 strategy_fund.xlsx → 3개 전략 테이블 업로드 완료!")
