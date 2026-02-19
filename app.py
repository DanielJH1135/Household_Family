import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 시트 주소 (이미지에 나온 그대로 입력했습니다)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLcO0SVOOKVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?gid=1035469932&single=true&output=csv"

def load_data():
    try:
        # 404 에러 방지를 위해 URL을 순수하게 유지합니다.
        df = pd.read_csv(SHEET_CSV_URL)
        
        # 날짜 처리: '타임스탬프'가 아닌 사용자님이 만든 '날짜' 컬럼을 기준으로 잡습니다.
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        else:
            # '날짜' 컬럼이 없으면 첫 번째 컬럼(타임스탬프) 사용
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            
        # 날짜 변환 실패한 행 삭제
        df = df.dropna(subset=[df.columns[0]])
        
        # 금액 처리: 문자열 콤마 제거 후 숫자로 변환
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"❌ 시트 연결 실패: {e}")
        return pd.DataFrame()

# 페이지 설정
st.set_page_config(page_title="🏡 우리집 자산관리", layout="wide")

st.title("💰 부부 공동 자산 관리 대시보드")

# 데이터 로드
df = load_data()

if not df.empty:
    now = datetime.now()
    # 이번 달 데이터 필터링 (사용자님이 입력한 '날짜' 컬럼 기준)
    # '날짜' 컬럼이 있으면 그걸 쓰고, 없으면 타임스탬프 기준
    date_col = '날짜' if '날짜' in df.columns else df.columns[0]
    this_month_df = df[pd.to_datetime(df[date_col]).dt.month == now.month]

    # --- 1구역: 입금 현황 ---
    st.subheader(f"💵 {now.month}월 공동 자금 입금 현황")
    col1, col2, col3 = st.columns(3)

    target_me = 1580000
    target_wife = 1220000
    
    # 주체와 구분 컬럼이 있는지 확인 후 계산
    if '주체' in df.columns and '구분' in df.columns:
        in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
        in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
        
        with col1:
            st.metric("나 (20일)", f"{in_me:,.0f}원", f"{in_me - target_me:,.0f}원")
        with col2:
            st.metric("와이프 (5일)", f"{in_wife:,.0f}원", f"{in_wife - target_wife:,.0f}원")
        with col3:
            total_in = in_me + in_wife
            progress = min(total_in / 2800000, 1.0)
            st.write(f"**공동자금(280만) 달성률: {progress*100:.1f}%**")
            st.progress(progress)

    # --- 2구역: 세이프박스 & 지출 ---
    st.divider()
    c_a, c_b = st.columns(2)
    
    with c_a:
        st.subheader("📦 세이프박스 (잔액)")
        total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
        # 이론적 잔액 (입금 - 지출)
        safe_calc = (in_me + in_wife) - total_out
        st.info(f"계산상 여유 자금: **{safe_calc:,.0f}원**")
        
        # 수동 업데이트 기록 표시
        actual_safe = df[df['구분'].str.contains('저축|세이프', na=False)].tail(1)
        if not actual_safe.empty:
            st.success(f"최근 수동 업데이트 잔액: **{actual_safe['금액'].values[0]:,.0f}원**")

    with c_b:
        st.subheader("💸 이번 달 지출 합계")
        st.error(f"현재까지 지출: **{total_out:,.0f}원**")

    # --- 3구역: 고정비 체크리스트 ---
    st.divider()
    st.subheader("✅ 필수 지출 체크리스트")
    
    fixed_items = {
        "주담대 (125만)": "주택담보|주담대|보금자리",
        "나의 신용대출 (47.6만)": "신용대출",
        "공동 관리비": "관리비"
    }
    
    cols = st.columns(len(fixed_items))
    for i, (name, kw) in enumerate(fixed_items.items()):
        # '항목' 컬럼에서 키워드 찾기
        is_done = not this_month_df[this_month_df['항목'].str.contains(kw, na=False)].empty
        with cols[i]:
            if is_done: st.success(f"**{name}**\n\n완료")
            else: st.warning(f"**{name}**\n\n대기")

    # --- 4구역: 전체 데이터 ---
    st.divider()
    st.subheader("📑 최근 거래 내역")
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
else:
    st.warning("시트에 데이터가 없거나 연결에 실패했습니다.")
