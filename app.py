import streamlit as st
import pandas as pd
from datetime import datetime

# [필독] 여기에 본인의 구글 시트 웹 게시(CSV) URL을 따옴표 안에 넣으세요
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        # 1. 날짜 처리: 첫 번째 컬럼(타임스탬프)을 강제로 날짜형으로 변환
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
        # 2. 날짜 변환 실패한 행(빈 줄 등) 삭제
        df = df.dropna(subset=[df.columns[0]])
        # 3. 금액 처리: 문자열인 경우 콤마 제거 후 숫자로 변환
        df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"시트 데이터를 읽어오는 중 에러 발생: {e}")
        return pd.DataFrame()

# 페이지 설정
st.set_page_config(page_title="🏡 우리집 통합 자산관리", layout="wide")

# 데이터 로드
df = load_data()

if not df.empty:
    now = datetime.now()
    # 이번 달 데이터만 필터링 (에러 방지를 위해 .dt 접근 전 형식 재확인)
    df['temp_date'] = pd.to_datetime(df.iloc[:, 0])
    this_month_df = df[df['temp_date'].dt.month == now.month]

    st.title(f"📊 {now.month}월 공동 자산 & 세이프박스")

    if this_month_df.empty:
        st.warning(f"⚠️ {now.month}월에 입력된 데이터가 아직 없습니다. 설문지를 먼저 작성해 주세요!")
    else:
        # --- 1구역: 입금 현황 ---
        st.subheader("💰 공동 자금 입금 (목표 280만)")
        c1, c2, c3 = st.columns(3)
        
        in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출'))]['금액'].sum()
        in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출'))]['금액'].sum()
        total_in = in_me + in_wife
        
        with c1:
            # 급여일: 나 20일 / 와이프 5일
            st.metric("나 (20일 급여)", f"{in_me:,.0f}원", f"{in_me - 1580000:,.0f}원")
        with c2:
            st.metric("와이프 (5일 급여)", f"{in_wife:,.0f}원", f"{in_wife - 1220000:,.0f}원")
        with c3:
            target_ratio = min(total_in / 2800000, 1.0)
            st.write(f"**전체 입금 달성률: {target_ratio*100:.1f}%**")
            st.progress(target_ratio)

        # --- 2구역: 세이프박스 요약 ---
        st.divider()
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("📦 세이프박스 현황")
            # 공동 지출 합계
            total_out = this_month_df[this_month_df['구분'].str.contains('지출')]['금액'].sum()
            # 이론적 잔액 = 들어온 돈 - 나간 돈
            theoretical_safe = total_in - total_out
            
            # 수동 업데이트: '저축(세이프박스)' 구분에 '세이프박스 정산' 항목이 있는지 확인
            actual_safe_entry = df[df['구분'].str.contains('저축')].tail(1)
            
            st.info(f"계산상 잔액: **{theoretical_safe:,.0f}원**")
            if not actual_safe_entry.empty:
                st.success(f"최근 수동 업데이트 잔액: **{actual_safe_entry['금액'].values[0]:,.0f}원**")

        with col_b:
            st.subheader("💸 이번 달 총 지출")
            st.error(f"현재까지 지출 합계: **{total_out:,.0f}원**")

        # --- 3구역: 고정 지출 체크리스트 ---
        st.divider()
        st.subheader("✅ 필수 지출 체크리스트")
        # 주담대 125만, 신용대출 47.6만 등
        check_list = {
            "주택담보대출 (125만)": "주택담보|주담대",
            "나의 신용대출 (47.6만)": "신용대출",
            "공동 관리비": "관리비"
        }
        
        check_cols = st.columns(len(check_list))
        for i, (name, keyword) in enumerate(check_list.items()):
            # 항목명에 키워드가 포함되어 있는지 확인
            is_done = not this_month_df[this_month_df['항목'].str.contains(keyword, na=False)].empty
            with check_cols[i]:
                if is_done:
                    st.success(f"**{name}**\n\n완료")
                else:
                    st.warning(f"**{name}**\n\n대기 중")

        # --- 4구역: 데이터 표 ---
        st.divider()
        st.subheader("📑 최근 내역 전체")
        st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
else:
    st.error("데이터를 불러오지 못했습니다. 구글 시트의 '웹에 게시' 설정을 확인해 주세요.")

