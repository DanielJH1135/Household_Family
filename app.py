import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# 1. 시트 주소 (사용자님 주소)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    try:
        # 캐시 방지용 쿼리 추가
        df = pd.read_csv(f"{SHEET_CSV_URL}&t={datetime.now().timestamp()}")
        
        # [핵심] 날짜 변환 로직 강화: 한국어 오전/오후 처리
        date_col = df.columns[0] # 타임스탬프 열
        df[date_col] = df[date_col].astype(str).str.replace('오후', 'PM').str.replace('오전', 'AM')
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # 날짜 변환 실패한 행 삭제
        df = df.dropna(subset=[date_col])
        
        # 금액 숫자 변환
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

st.set_page_config(page_title="우리집 통합 대시보드", layout="wide")
df = load_data()

if not df.empty:
    # 조회용 연월(Year-Month) 컬럼 생성
    df['YearMonth'] = df.iloc[:, 0].dt.strftime('%Y-%m')
    all_months = sorted(df['YearMonth'].unique(), reverse=True)
    
    # 사이드바 설정
    st.sidebar.header("📅 조회 설정")
    selected_month = st.sidebar.selectbox("조회할 달 선택", all_months, index=0)
    
    # 선택된 달 데이터 필터링
    this_month_df = df[df['YearMonth'] == selected_month]
    
    st.title(f"📊 {selected_month} 자산 현황")
    
    # --- 1층: 입금 지표 ---
    col1, col2, col3 = st.columns([1, 1, 2])
    # 입금액 계산 (나 1.58M / 와이프 1.22M)
    in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    
    with col1:
        st.metric("🤵 나 (20일)", f"{in_me:,.0f}원", f"{in_me - 1580000:,.0f}원")
    with col2:
        st.metric("👰 와이프 (5일)", f"{in_wife:,.0f}원", f"{in_wife - 1220000:,.0f}원")
    with col3:
        total_in = in_me + in_wife
        progress = min(total_in / 2800000, 1.0)
        st.write(f"**💰 공동 자금 달성률: {progress*100:.1f}%**")
        st.progress(progress)

    st.divider()

    # --- 2층: 차트 분석 ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🍕 지출 비중")
        exp_df = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]
        if not exp_df.empty:
            fig = px.pie(exp_df, values='금액', names='항목', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("기록된 지출 내역이 없습니다.")

    with c2:
        st.subheader("📈 저축 흐름")
        monthly_flow = df.groupby('YearMonth').apply(
            lambda x: x[x['구분'].str.contains('각출|입금', na=False)]['금액'].sum() - 
                      x[x['구분'].str.contains('지출', na=False)]['금액'].sum()
        ).reset_index(name='Balance')
        fig2 = px.line(monthly_flow, x='YearMonth', y='Balance', markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    # --- 3층: 체크리스트 ---
    st.divider()
    st.subheader("✅ 고정비 체크리스트")
    total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
    st.info(f"📦 세이프박스 이관 가능 금액: **{(total_in - total_out):,.0f}원**")
    
    checklist_cols = st.columns(3)
    # 체증식 주담대 등 고정비 키워드 매칭
    items = {"🏠 주담대": "주택담보|주담대", "💳 신용대출": "신용대출", "🏢 관리비": "관리비"}
    for i, (name, kw) in enumerate(items.items()):
        match = this_month_df[this_month_df['항목'].str.contains(kw, na=False)]
        with checklist_cols[i]:
            if not match.empty:
                st.success(f"{name} 완료\n\n({match['금액'].sum():,.0f}원)")
            else:
                st.info(f"{name} 대기 중")

    with st.expander("📑 전체 내역 보기"):
        st.dataframe(this_month_df.sort_values(by=this_month_df.columns[0], ascending=False), use_container_width=True)
else:
    st.warning("시트에 데이터가 없거나 형식이 맞지 않습니다. 설문지를 확인해 주세요.")
