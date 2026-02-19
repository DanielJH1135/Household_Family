import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 시트 주소 (사용자님 주소 그대로 유지)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRddSb69D6MnJFwXrsENh-MV8UsGlYYLc00Sv0KVd7N2d7T5tM740qmW1ao1gGa-k5ypGl82F9M6LDR/pub?output=csv"

def load_data():
    try:
        # 캐시 방지를 위해 현재 시간을 쿼리에 살짝 섞어줍니다.
        df = pd.read_csv(f"{SHEET_CSV_URL}&t={datetime.now().timestamp()}")
        
        # [데이터 보정] 금액 컬럼이 비어있거나 밀리는 경우 대비
        # '금액' 컬럼의 콤마 제거 및 숫자 변환
        if '금액' in df.columns:
            df['금액'] = pd.to_numeric(df['금액'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 날짜 처리 (한국어 '오후/오전' 포함 형식 대응)
        date_col = '날짜' if '날짜' in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col].astype(str).str.replace('오후', 'PM').str.replace('오전', 'AM'), errors='coerce')
        
        return df.dropna(subset=[df.columns[2]]) # 구분이 비어있는 행 제외
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# --- 페이지 설정 (대시보드 스타일) ---
st.set_page_config(page_title="우리집 통합 대시보드", layout="wide")

# 사이드바 없이 메인 화면에 한 페이지로 구성
df = load_data()

if not df.empty:
    now = datetime.now()
    # 이번 달 데이터 필터링
    date_col = '날짜' if '날짜' in df.columns else df.columns[0]
    this_month_df = df[df[date_col].dt.month == now.month]

    st.title(f"☀️ {now.month}월 공동 자산 에너지 대시보드")
    
    # --- 1층: 입금 및 목표 현황 (3분할) ---
    col1, col2, col3 = st.columns([1, 1, 2])
    
    # 입금액 계산 (정확하게 '각출' 문구 포함 행만)
    in_me = this_month_df[(this_month_df['주체'] == '나') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    in_wife = this_month_df[(this_month_df['주체'] == '와이프') & (this_month_df['구분'].str.contains('각출|입금', na=False))]['금액'].sum()
    
    with col1:
        st.metric("🤵 나 (20일 급여)", f"{in_me:,.0f}원", f"{in_me - 1580000:,.0f}원")
    with col2:
        st.metric("👰 와이프 (5일 급여)", f"{in_wife:,.0f}원", f"{in_wife - 1220000:,.0f}원")
    with col3:
        total_in = in_me + in_wife
        target = 2800000
        progress = min(total_in / target, 1.0)
        st.write(f"**💰 공동 자금 충전량: {progress*100:.1f}%** ({total_in:,.0f} / {target:,.0f})")
        st.progress(progress)

    st.divider()

    # --- 2층: 지출 및 세이프박스 (좌우 2분할) ---
    left_col, right_col = st.columns(2)
    
    with left_col:
        st.subheader("📦 세이프박스 (잔액)")
        # 총 지출액 계산 (키워드: '지출')
        total_out = this_month_df[this_month_df['구분'].str.contains('지출', na=False)]['금액'].sum()
        safe_calc = (in_me + in_wife) - total_out
        
        # 실제 세이프박스 수동 입력 기록 확인
        manual_safe = df[df['구분'].str.contains('저축|세이프', na=False)].tail(1)
        
        c_a, c_b = st.columns(2)
        c_a.info(f"계산상 잔액\n\n**{safe_calc:,.0f}원**")
        if not manual_safe.empty:
            c_b.success(f"수동 정산 금액\n\n**{manual_safe['금액'].values[0]:,.0f}원**")
        else:
            c_b.warning("수동 정산 기록 없음")

    with right_col:
        st.subheader("💸 지출 현황 요약")
        st.error(f"이번 달 누적 지출: **{total_out:,.0f}원**")
        # 생활비 소진율 (공동자금 대비 얼마나 썼는지)
        usage_rate = (total_out / total_in * 100) if total_in > 0 else 0
        st.write(f"현재 입금액 대비 **{usage_rate:.1f}%** 소진 중")

    st.divider()

    # --- 3층: 체크리스트 (가로 한 줄) ---
    st.subheader("✅ 고정비 상환 체크")
    checklist_cols = st.columns(3)
    items = {
        "🏠 주담대 (125만)": "주택담보|주담대|보금자리",
        "💳 신용대출 (47.6만)": "신용대출",
        "🏢 관리비": "관리비"
    }
    
    for i, (name, kw) in enumerate(items.items()):
        is_done = not this_month_df[this_month_df['항목'].str.contains(kw, na=False)].empty
        with checklist_cols[i]:
            if is_done: st.success(f"{name} 완료")
            else: st.info(f"{name} 대기 중")

    # --- 4층: 데이터 테이블 (접기 메뉴로 깔끔하게) ---
    with st.expander("📑 전체 거래 내역 보기"):
        st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)

else:
    st.error("데이터를 읽어올 수 없습니다. 시트의 데이터가 코드의 컬럼명과 일치하는지 확인해 주세요.")
