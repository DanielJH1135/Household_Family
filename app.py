import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px # 차트를 위해 추가

# 1. 시트 주소
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    try:
        df = pd.read_csv(f"{SHEET_CSV_URL}&t={datetime.now().timestamp()}")
        # 날짜 컬럼 처리
        date_col = '날짜' if '날짜' in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col].astype(str).str.replace('오후', 'PM').str.replace('오전', 'AM'), errors='coerce')
        # 금액 처리
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df.dropna(subset=[df.columns[2]])
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

st.set_page_config(page_title="우리집 통합 대시보드", layout="wide")
df = load_data()

if not df.empty:
    # --- 상단 설정: 월 선택 기능 (자동으로 현재 달 선택) ---
    st.sidebar.header("📅 조회 설정")
    df['YearMonth'] = df.iloc[:, 0].dt.to_period('M').astype(str)
    all_months = sorted(df['YearMonth'].unique(), reverse=True)
    selected_month = st.sidebar.selectbox("조회할 달을 선택하세요", all_months, index=0)
    
    this_month_df = df[df['YearMonth'] == selected_month]
    
    st.title(f"📊 {selected_month} 자산 대시보드")
    
    # --- 1층: 입금 현황 ---
    col1, col2, col3 = st.columns([1, 1, 2])
    in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    
    with col1:
        st.metric("🤵 나 입금", f"{in_me:,.0f}원", f"{in_me - 1580000:,.0f}원")
    with col2:
        st.metric("👰 와이프 입금", f"{in_wife:,.0f}원", f"{in_wife - 1220000:,.0f}원")
    with col3:
        total_in = in_me + in_wife
        progress = min(total_in / 2800000, 1.0)
        st.write(f"**💰 공동 자금 달성률: {progress*100:.1f}%**")
        st.progress(progress)

    st.divider()

    # --- 2층: 차트 분석 (신규!) ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🍕 지출 카테고리 비중")
        exp_df = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]
        if not exp_df.empty:
            fig = px.pie(exp_df, values='금액', names='항목', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("지출 내역이 없습니다.")

    with c2:
        st.subheader("📈 월별 저축(잔액) 흐름")
        # 월별로 (입금합계 - 지출합계) 계산
        monthly_flow = df.groupby('YearMonth').apply(
            lambda x: x[x['구분'].str.contains('각출|입금', na=False)]['금액'].sum() - 
                      x[x['구분'].str.contains('지출', na=False)]['금액'].sum()
        ).reset_index()
        monthly_flow.columns = ['Month', 'Balance']
        fig2 = px.line(monthly_flow, x='Month', y='Balance', markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # --- 3층: 체크리스트 & 세이프박스 ---
    total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
    st.info(f"📦 현재 세이프박스로 보낼 수 있는 돈: **{(total_in - total_out):,.0f}원**")
    
    # 체크리스트 로직은 동일...
    checklist_cols = st.columns(3)
    items = {"🏠 주담대": "주택담보|주담대", "💳 신용대출": "신용대출", "🏢 관리비": "관리비"}
    for i, (name, kw) in enumerate(items.items()):
        is_done = not this_month_df[this_month_df['항목'].str.contains(kw, na=False)].empty
        with checklist_cols[i]:
            if is_done: st.success(f"{name} 완료")
            else: st.info(f"{name} 대기 중")

    with st.expander("📑 전체 내역 보기"):
        st.dataframe(this_month_df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
