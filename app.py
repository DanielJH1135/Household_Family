import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 구글 시트 웹 게시(CSV) URL (여기에 본인의 URL을 넣으세요)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    # 첫 번째 컬럼(타임스탬프 또는 날짜)을 날짜 형식으로 변환
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
    # 금액 컬럼 숫자 변환 및 결측치 처리
    df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    return df

st.set_page_config(page_title="🏡 우리집 자산관리 시스템", layout="wide")

try:
    df = load_data()
    now = datetime.now()
    # 이번 달 데이터만 추출
    this_month_df = df[df.iloc[:, 0].dt.month == now.month]

    st.title(f"📊 {now.month}월 가계부 & 세이프박스")

    # --- 1구역: 공동자금 입금 현황 (나 158만 / 와이프 122만) ---
    st.subheader("💰 공동 자금 입금 (목표 280만)")
    c1, c2, c3 = st.columns(3)
    
    in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'] == '각출(공동입금)')]['금액'].sum()
    in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'] == '각출(공동입금)')]['금액'].sum()
    total_in = in_me + in_wife
    
    with c1:
        st.metric("나 (20일)", f"{in_me:,.0f}원", f"{in_me - 1580000:,.0f}원")
    with c2:
        st.metric("와이프 (5일)", f"{in_wife:,.0f}원", f"{in_wife - 1220000:,.0f}원")
    with c3:
        target_ratio = min(total_in / 2800000, 1.0)
        st.write(f"**전체 달성률: {target_ratio*100:.1f}%**")
        st.progress(target_ratio)

    # --- 2구역: 세이프박스 & 지출 요약 ---
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📦 세이프박스 현황")
        total_out = this_month_df[this_month_df['구분'] == '지출(공동)']['금액'].sum()
        theoretical_safe = total_in - total_out
        
        # 마지막으로 입력된 '저축(세이프박스)' 항목이 있다면 실제 잔액으로 표시
        actual_safe_entry = df[df['구분'] == '저축(세이프박스)'].tail(1)
        
        st.info(f"현재 이동 가능한 여유 자금: **{theoretical_safe:,.0f}원**")
        if not actual_safe_entry.empty:
            st.success(f"최근 기록된 실제 세이프박스 잔액: **{actual_safe_entry['금액'].values[0]:,.0f}원**")

    with col_b:
        st.subheader("💸 이번 달 총 지출")
        st.error(f"현재까지 지출 합계: **{total_out:,.0f}원**")

    # --- 3구역: 고정 지출 체크리스트 ---
    st.divider()
    st.subheader("✅ 필수 지출 체크리스트")
    
    # 체크할 항목들과 키워드 설정
    check_list = {
        "주택담보대출 (125만)": "주택담보|주담대",
        "나의 신용대출 (47.6만)": "신용대출",
        "공동 관리비": "관리비"
    }
    
    check_cols = st.columns(len(check_list))
    for i, (name, keyword) in enumerate(check_list.items()):
        is_done = not this_month_df[this_month_df['항목'].str.contains(keyword, na=False)].empty
        with check_cols[i]:
            if is_done:
                st.success(f"**{name}**\n\n이체 완료")
            else:
                st.warning(f"**{name}**\n\n대기 중")

    # --- 4구역: 전체 내역 데이터 ---
    st.divider()
    st.subheader("📑 전체 내역 상세보기")
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다. URL을 확인하세요. 에러: {e}")

