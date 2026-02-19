import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 시트 주소 설정 (사용자님이 게시하신 URL 그대로 넣었습니다)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLcO0SVOOKVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?gid=1035469932&single=true&output=csv"

def load_data():
    try:
        # 데이터 읽기 (캐시 방지를 위해 랜덤 쿼리 추가)
        df = pd.read_csv(f"{SHEET_CSV_URL}&cache={datetime.now().timestamp()}")
        
        # 날짜 처리: 첫 번째 컬럼(타임스탬프)을 날짜형으로
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        df = df.dropna(subset=[df.columns[0]])
        
        # 금액 처리: 문자열 콤마 제거 후 숫자로
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        return pd.DataFrame()

# 페이지 설정
st.set_page_config(page_title="🏡 우리집 자산관리 시스템", layout="wide")

st.title("💰 부부 공동 자산 관리 대시보드")

# 데이터 로드
df = load_data()

# --- 데이터 검증 로직 ---
if df.empty:
    st.warning("⚠️ 시트에서 데이터를 가져오지 못했습니다. 설문지 응답이 최소 1개 이상 있는지 확인해 주세요.")
    st.info("💡 팁: 구글 시트에서 '웹에 게시' 버튼을 누른 후 실제 데이터가 반영되기까지 1~2분 정도 걸릴 수 있습니다.")
else:
    # 컬럼 이름이 코드와 맞는지 확인하기 위한 디버그 (성공하면 삭제 가능)
    with st.expander("🛠️ 데이터 구조 확인 (에러 발생 시 참고)"):
        st.write("시트의 컬럼 이름들:", df.columns.tolist())
    
    now = datetime.now()
    # 이번 달 데이터 필터링
    this_month_df = df[df.iloc[:, 0].dt.month == now.month]
    
    # --- 1구역: 입금 현황 ---
    st.subheader(f"💵 {now.month}월 공동 자금 입금 현황")
    col1, col2, col3 = st.columns(3)

    # 타겟 금액 설정
    target_me = 1580000
    target_wife = 1220000
    
    # 데이터 계산 (컬럼명이 '주체', '구분'인 경우)
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
    else:
        st.error("❗ 시트에 '주체' 또는 '구분' 컬럼이 보이지 않습니다. 설문지 질문 제목을 확인하세요.")

    # --- 2구역: 세이프박스 & 지출 ---
    st.divider()
    c_a, c_b = st.columns(2)
    
    with c_a:
        st.subheader("📦 세이프박스 (잔액)")
        # 총 입금액 - 총 지출액
        total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
        safe_calc = (in_me + in_wife) - total_out
        st.info(f"계산상 여유 자금: **{safe_calc:,.0f}원**")
        
        # 수동 업데이트 기록이 있다면 표시
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
        "주담대 (125만)": "주택담보|주담대",
        "신용대출 (47.6만)": "신용대출",
        "공동 관리비": "관리비"
    }
    
    cols = st.columns(len(fixed_items))
    for i, (name, kw) in enumerate(fixed_items.items()):
        is_done = not this_month_df[this_month_df['항목'].str.contains(kw, na=False)].empty
        with cols[i]:
            if is_done: st.success(f"**{name}**\n\n완료")
            else: st.warning(f"**{name}**\n\n대기")

    # --- 4구역: 전체 데이터 ---
    st.divider()
    st.subheader("📑 최근 거래 내역")
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
