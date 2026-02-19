import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 시트 주소
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    try:
        df = pd.read_csv(f"{SHEET_CSV_URL}&t={datetime.now().timestamp()}")
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        date_col = '날짜' if '날짜' in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col].astype(str).str.replace('오후', 'PM').str.replace('오전', 'AM'), errors='coerce')
        return df.dropna(subset=[df.columns[2]])
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

st.set_page_config(page_title="우리집 통합 대시보드", layout="wide")
df = load_data()

if not df.empty:
    now = datetime.now()
    date_col = '날짜' if '날짜' in df.columns else df.columns[0]
    this_month_df = df[df[date_col].dt.month == now.month]

    st.title(f"☀️ {now.month}월 공동 자산 대시보드")
    
    # --- 1층: 입금 및 목표 현황 ---
    col1, col2, col3 = st.columns([1, 1, 2])
    in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    
    with col1:
        st.metric("🤵 나 (20일)", f"{in_me:,.0f}원", f"{in_me - 1580000:,.0f}원")
    with col2:
        st.metric("👰 와이프 (5일)", f"{in_wife:,.0f}원", f"{in_wife - 1220000:,.0f}원")
    with col3:
        total_in = in_me + in_wife
        target = 2800000
        progress = min(total_in / target, 1.0)
        st.write(f"**💰 공동 자금 달성률: {progress*100:.1f}%**")
        st.progress(progress)

    st.divider()

    # --- 2층: 지출 및 세이프박스 ---
    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("📦 세이프박스 (잔액)")
        total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
        safe_calc = total_in - total_out
        st.info(f"계산상 여유 자금: **{safe_calc:,.0f}원**")

    with right_col:
        st.subheader("💸 지출 요약")
        st.error(f"이번 달 누적 지출: **{total_out:,.0f}원**")

    st.divider()

    # --- 3층: 가변적 체크리스트 (핵심!) ---
    st.subheader("✅ 필수 지출 체크리스트")
    checklist_cols = st.columns(3)
    
    # 주담대 체크 로직 (금액 고정 X, 항목 이름으로만 판단)
    mortgage_data = this_month_df[this_month_df['항목'].str.contains("주택담보|주담대|보금자리", na=False)]
    loan_data = this_month_df[this_month_df['항목'].str.contains("신용대출", na=False)]
    bill_data = this_month_df[this_month_df['항목'].str.contains("관리비", na=False)]

    with checklist_cols[0]:
        if not mortgage_data.empty:
            paid_amt = mortgage_data['금액'].sum()
            st.success(f"🏠 주담대 완료\n\n**{paid_amt:,.0f}원** 지출됨")
        else:
            st.info("🏠 주담대\n\n대기 중")

    with checklist_cols[1]:
        if not loan_data.empty:
            paid_amt = loan_data['금액'].sum()
            st.success(f"💳 신용대출 완료\n\n**{paid_amt:,.0f}원** 지출됨")
        else:
            st.info("💳 신용대출\n\n대기 중")

    with checklist_cols[2]:
        if not bill_data.empty:
            paid_amt = bill_data['금액'].sum()
            st.success(f"🏢 관리비 완료\n\n**{paid_amt:,.0f}원** 지출됨")
        else:
            st.info("🏢 관리비\n\n대기 중")

    st.divider()
    with st.expander("📑 전체 거래 내역 보기"):
        st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)

else:
    st.error("데이터를 읽어올 수 없습니다.")
