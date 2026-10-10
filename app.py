import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(page_title="KBO 타자 MVP 점수 계산기", layout="centered")
st.title("⚾ KBO 타자 MVP 점수 산출 프로그램")
st.caption(
    "상관관계 분석 기반 가중치: 장타율(37.3%) + 타율(33.1%) + 출루율(29.6%)"
)


# 2. 데이터 로드 함수 (캐싱 적용)
@st.cache_data
def load_data():
    excel_path = "KBO_타자투수_통합_마스터_한글지표_출루율OPS추가.xlsx"
    df = pd.read_excel(excel_path, sheet_name="타자_MASTER_2010_2025")

    # 수치형 데이터 변환 및 정제
    num_cols = ["연도", "타율", "출루율", "장타율", "OPS", "경기", "타석", "홈런"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df_batter = load_data()

# 3. 가중치 정의
W_SLG = 0.373  # 장타율 가중치 (37.3%)
W_AVG = 0.331  # 타율 가중치 (33.1%)
W_OBP = 0.296  # 출루율 가중치 (29.6%)

# 4. 사용자 입력 폼
st.subheader("🔍 선수 성적 및 MVP 점수 조회")
col1, col2 = st.columns(2)

with col1:
    # 엑셀 데이터 내 사용 가능한 연도 목록 추출
    available_years = sorted(
        df_batter["연도"].dropna().unique().astype(int), reverse=True
    )
    selected_year = st.selectbox("연도를 선택하세요", available_years)

with col2:
    player_name = st.text_input(
        "선수 이름을 입력하세요", placeholder="예: 김도영, 디아즈"
    )

# 5. 조회 및 MVP 점수 계산 버튼
if st.button("MVP 점수 계산하기"):
    if not player_name.strip():
        st.warning("선수 이름을 입력해주세요.")
    else:
        # 데이터 검색
        result = df_batter[
            (df_batter["연도"] == selected_year)
            & (df_batter["선수명"].str.contains(player_name, na=False))
        ]

        if result.empty:
            st.error(
                f"❌ {selected_year}년도 데이터에서 '{player_name}' 선수를 찾을 수 없습니다."
            )
        else:
            for _, row in result.iterrows():
                slg = row["장타율"]
                avg = row["타율"]
                obp = row["출루율"]

                # 가중합 계산
                mvp_score = (slg * W_SLG) + (avg * W_AVG) + (obp * W_OBP)

                # 결과 출력 카드
                st.success(
                    f"### 🏆 {row['연도']}년 {row['선수명']} ({row['팀']})"
                )

                metric_col1, metric_col2, metric_col3, metric_col4 = (
                    st.columns(4)
                )
                metric_col1.metric("타율 (AVG)", f"{avg:.3f}")
                metric_col2.metric("출루율 (OBP)", f"{obp:.3f}")
                metric_col3.metric("장타율 (SLG)", f"{slg:.3f}")
                metric_col4.metric("🌟 MVP 점수", f"{mvp_score:.4f}")

                st.write(
                    f"**계산식**: `({slg:.3f} × 0.373) + ({avg:.3f} × 0.331) + ({obp:.3f} × 0.296) = {mvp_score:.4f}`"
                )
                st.markdown("---")