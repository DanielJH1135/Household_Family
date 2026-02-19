import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 시트 주소 (이미지에 나온 URL 그대로 정확히 입력했습니다)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLcO0SVOOKVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?gid=1035469932&single=true&output=csv"

def load_data():
    try:
        # 404 에러 방지를 위해 군더더기 없는 순수 URL로 읽어옵니다.
        df = pd.read_csv(SHEET_CSV_URL)
        
        # 날짜 처리: '타임스탬프'가 아닌 사용자님이 만든 '날짜' 컬럼을 기준으로 잡습니다.
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
        else:
            # '날짜' 컬럼이 없으면 첫 번째 컬럼(타임스탬프) 사용
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            
        # 데이터 정제: 날짜 변환 실패한 빈 줄 등 삭제
        df = df.dropna(subset=[df.columns[0]])
        
        # 금액 처리: 문자열 콤마 제거 후 숫자로 변환
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        # 에러 발생 시 사용자에게 명확한 이유를 보여줍니다.
        st.error(f"❌ 시트 연결 실패: {e}")
        return pd.DataFrame()

# 스트림릿 페이지 설정
st.set_page_config(page_title="🏡 우리집 자산관리", layout="wide")

st.title("💰 부부 공동 자산 관리 대시보드")

# 데이터 불러오기
df = load_data()

if not df.empty:
    now = datetime.now()
    # 이번 달 데이터 필터링 (사용자님의 '날짜' 컬럼 기준)
    date_col = '날짜' if '날짜' in df.columns else df.columns[0]
    this_month_df = df[pd.to_datetime(df[date_col]).dt.month == now.month]

    # --- 1구역: 입금 현황 (나 158만 / 와이프 122만) ---
    st.subheader(f"💵 {now.month}월 공동 자금 입금 현황")
    col1, col2, col3 = st.columns(3)

    target_me = 1580000
    target_wife = 1220000
    
    # '주체'와 '구분' 컬럼 데이터를 기반으로 계산
    in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    
    with col1:
        # 나의 급여일은 20일
        st.metric("나 (20일 급여)", f"{in_me:,.0f}원", f"{in_me - target_me:,.0f}원")
    with col2:
        # 와이프 급여일은 5일
        st.metric("와이프 (5일 급여)", f"{in_wife:,.0f}원", f"{in_wife - target_wife:,.0f}원")
    with col3:
        total_in = in_me + in_wife
        progress = min(total_in / 2800000, 1.0)
        st.write(f"**공동자금 목표(280만) 달성률: {progress*100:.1f}%**")
        st.progress(progress)

    # --- 2구역: 세이프박스 & 지출 ---
    st.divider()
    c_a, c_b = st.columns(2)
    
    with c_a:
        st.subheader("📦 세이프박스 (잔액)")
        total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
        # 이론적 잔액 (총 입금 - 총 지출)
        safe_calc = total_in - total_out
        st.info(f"계산상 여유 자금: **{safe_calc:,.0f}원**")
        
        # 최근 기록된 세이프박스 실제 잔액이 있는지 확인
        actual_safe = df[df['구분'].str.contains('저축|세이프', na=False)].tail(1)
        if not actual_safe.empty:
            st.success(f"최근 수동 업데이트 잔액: **{actual_safe['금액'].values[0]:,.0f}원**")

    with c_b:
        st.subheader("💸 이번 달 지출 합계")
        st.error(f"현재까지 지출: **{total_out:,.0f}원**")

    # --- 3구역: 고정비 체크리스트 ---
    st.divider()
    st.subheader("✅ 필수 지출 체크리스트")
    
    # 주담대 125만, 신용대출 47.6만 기준
    fixed_items = {
        "주담대 (125만)": "주택담보|주담대|보금자리",
        "나의 신용대출 (47.6만)": "신용대출",
        "공동 관리비": "관리비"
    }
    
    cols = st.columns(len(fixed_items))
    for i, (name, kw) in enumerate(fixed_items.items()):
        is_done = not this_month_df[this_month_df['항목'].str.contains(kw, na=False)].empty
        with cols[i]:
            if is_done: st.success(f"**{name}**\n\n완료")
            else: st.warning(f"**{name}**\n\n대기 중")

    # --- 4구역: 전체 데이터 내역 ---
    st.divider()
    st.subheader("📑 최근 기록 전체보기")
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)

else:
    st.warning("시트에 데이터가 없거나 구글에서 데이터를 쏴주지 않고 있습니다. 잠시 후 새로고침 해보세요.")
