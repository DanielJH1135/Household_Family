import streamlit as st
import pandas as pd

# 1. 시트 설정 (여기에 복사한 CSV URL을 넣으세요)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    # CSV URL을 통해 데이터를 직접 읽어옵니다.
    df = pd.read_csv(SHEET_CSV_URL)
    # 금액 컬럼 숫자 변환
    df['금액'] = pd.to_numeric(df['금액'], errors='coerce').fillna(0)
    return df

st.set_page_config(page_title="우리집 가계부", layout="wide")

try:
    df = load_data()
    
    st.title("💰 부부 공동 자산 관리 (Plan B)")

    # 목표 금액 (사용자 요청 기반)
    TARGET_ME = 1580000
    TARGET_WIFE = 1220000
    TOTAL_TARGET = 2800000

    # 데이터 필터링 (간단하게 '각출' 내역 합산)
    actual_me = df[(df['주체'] == '나') & (df['구분'].str.contains('각출'))]['금액'].sum()
    actual_wife = df[(df['주체'] == '와이프') & (df['구분'].str.contains('각출'))]['금액'].sum()
    total_actual = actual_me + actual_wife

    # --- 대시보드 상단 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("나의 입금 (20일)", f"{actual_me:,.0f}원", f"{actual_me - TARGET_ME:,.0f}원")
    with col2:
        st.metric("와이프 입금 (5일)", f"{actual_wife:,.0f}원", f"{actual_wife - TARGET_WIFE:,.0f}원")
    with col3:
        progress = min(total_actual / TOTAL_TARGET, 1.0) if TOTAL_TARGET > 0 else 0
        st.write(f"**공동 자금 달성률: {progress*100:.1f}%**")
        st.progress(progress)

    # --- 알림 섹션 ---
    st.divider()
    st.subheader("📌 주요 지출 체크리스트")
    
    # 지출 여부 확인 로직
    loan_done = not df[(df['항목'].str.contains('주택담보대출')) & (df['상태'] == '완료')].empty
    my_loan_done = not df[(df['항목'].str.contains('신용대출')) & (df['상태'] == '완료')].empty

    c1, c2 = st.columns(2)
    with c1:
        if loan_done: st.success("✅ 주택담보대출 (125만) 처리됨")
        else: st.warning("⚠️ 주택담보대출 (125만) 예정")
    with c2:
        if my_loan_done: st.success("✅ 나의 신용대출 (47.6만) 처리됨")
        else: st.info("ℹ️ 나의 신용대출 (47.6만) 예정 (20일)")

    # --- 상세 내역 ---
    st.subheader("📑 최근 기록")
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)

except Exception as e:

    st.error(f"데이터를 불러올 수 없습니다. URL을 확인해주세요! 에러: {e}")
