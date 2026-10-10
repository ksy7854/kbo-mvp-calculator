import pandas as pd
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(page_title="KBO 타자 MVP 선택 모델", layout="wide")
st.title("⚾ KBO 타자 MVP 선택 모델 (규정 타석 적용)")
st.caption(
    "1차 비율 지표 가중합 모델: 장타율(37.3%) + 타율(33.1%) + 출루율(29.6%)"
)


# 2. 연도별 KBO 실제 MVP 타자 단독 수상 데이터 (2010~2025)
# (투수가 MVP를 수상한 해는 최우수 타자를 기재)
ACTUAL_MVPS = {
    2010: {"선수명": "이대호", "팀": "롯데"},
    2011: {"선수명": "최형우", "팀": "삼성"},  # (실제 MVP 윤석민 투수)
    2012: {"선수명": "박병호", "팀": "넥센"},
    2013: {"선수명": "박병호", "팀": "넥센"},
    2014: {"선수명": "서건창", "팀": "넥센"},
    2015: {"선수명": "테임즈", "팀": "NC"},
    2016: {"선수명": "최형우", "팀": "삼성"},  # (실제 MVP 니퍼트 투수)
    2017: {"선수명": "양의지", "팀": "두산"},  # (실제 MVP 양현종 투수)
    2018: {"선수명": "김재환", "팀": "두산"},
    2019: {"선수명": "박병호", "팀": "키움"},  # (실제 MVP 린드블럼 투수)
    2020: {"선수명": "로하스", "팀": "KT"},
    2021: {"선수명": "강백호", "팀": "KT"},  # (실제 MVP 미란다 투수)
    2022: {"선수명": "이정후", "팀": "키움"},
    2023: {"선수명": "노시환", "팀": "한화"},  # (실제 MVP 페디 투수)
    2024: {"선수명": "김도영", "팀": "KIA"},
    2025: {"선수명": "디아즈", "팀": "삼성"},
}


# 3. 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_process_data():
    excel_path = "KBO_타자투수_통합_마스터_한글지표_출루율OPS추가.xlsx"
    df = pd.read_excel(excel_path, sheet_name="타자_MASTER_2010_2025")

    # 수치형 변환
    num_cols = ["연도", "타율", "출루율", "장타율", "OPS", "경기", "타석", "홈런", "안타"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 가중치 산정 (SLG 37.3%, AVG 33.1%, OBP 29.6%)
    W_SLG, W_AVG, W_OBP = 0.373, 0.331, 0.296
    df["MVP점수"] = (
        (df["장타율"] * W_SLG) + (df["타율"] * W_AVG) + (df["출루율"] * W_OBP)
    )

    # 연도별 규정 타석 계산 (144경기 기준 446타석, 2014 이전은 396~412타석)
    # 규정타석 공식 = 팀 경기 수 * 3.1
    def get_qualified_pa(year):
        if year in [2010, 2011, 2012]:
            return 133 * 3.1  # 412타석
        elif year in [2013, 2014]:
            return 128 * 3.1  # 396타석
        else:
            return 144 * 3.1  # 446타석

    df["규정타석"] = df["연도"].apply(get_qualified_pa)
    df["규정타석충족"] = df["타석"] >= df["규정타석"]

    return df


df_batter = load_and_process_data()

# 4. 사이드바 - 연도 선택 및 규정 타석 필터 옵션
st.sidebar.header("⚙️ 분석 설정")
available_years = sorted(
    df_batter["연도"].dropna().unique().astype(int), reverse=True
)
selected_year = st.sidebar.selectbox("연도 선택", available_years)

only_qualified = st.sidebar.checkbox("규정 타석 충족자만 보기", value=True)

# 5. 선택 연도 데이터 필터링
df_year = df_batter[df_batter["연도"] == selected_year].copy()
if only_qualified:
    df_year = df_year[df_year["규정타석충족"]]

df_year = df_year.sort_values(by="MVP점수", ascending=False).reset_index(
    drop=True
)

# 6. 메인 화면 - 1위 vs 실제 MVP 비교 카드
st.subheader(f"📊 {selected_year}시즌 MVP 비교 결과")

if not df_year.empty:
    model_top = df_year.iloc[0]  # 수학 모델 1위

    col1, col2 = st.columns(2)

    # [좌측] 수학적 모델 선정 최고점 1위 타자
    with col1:
        st.success("🤖 **[모델 산출 1위] 최우수 타자**")
        st.markdown(f"### **{model_top['선수명']}** ({model_top['팀']})")
        st.metric("🌟 MVP 계산 점수", f"{model_top['MVP점수']:.4f}")
        st.write(
            f"• 타율: `{model_top['타율']:.3f}` | 출루율: `{model_top['출루율']:.3f}` | 장타율: `{model_top['장타율']:.3f}`"
        )
        st.write(
            f"• 타석: `{int(model_top['타석'])}` / `{int(model_top['홈런'])}홈런`"
        )

    # [우측] 해당 연도 실제 KBO MVP 타자
    with col2:
        actual_info = ACTUAL_MVPS.get(
            selected_year, {"선수명": "미정", "팀": "-"}
        )
        actual_player_data = df_batter[
            (df_batter["연도"] == selected_year)
            & (df_batter["선수명"] == actual_info["선수명"])
        ]

        st.info("🏆 **[실제 KBO] 수상 타자**")
        st.markdown(f"### **{actual_info['선수명']}** ({actual_info['팀']})")

        if not actual_player_data.empty:
            act_row = actual_player_data.iloc[0]
            st.metric("🌟 MVP 계산 점수", f"{act_row['MVP점수']:.4f}")
            st.write(
                f"• 타율: `{act_row['타율']:.3f}` | 출루율: `{act_row['출루율']:.3f}` | 장타율: `{act_row['장타율']:.3f}`"
            )
            st.write(
                f"• 타석: `{int(act_row['타석'])}` / `{int(act_row['홈런'])}홈런`"
            )
        else:
            st.write("해당 선수 데이터 검색 중...")

    # 두 결과가 일치하는지 판정
    st.markdown("---")
    if actual_info["선수명"] == model_top["선수명"]:
        st.balloons()
        st.success(
            f"🎯 **일치!** {selected_year}년 수학적 선택 모델 1위({model_top['선수명']})와 실제 KBO MVP가 정확히 일치합니다!"
        )
    else:
        st.warning(
            f"💡 **차이 발생!** {selected_year}년 모델 1위는 **{model_top['선수명']}**, 실제 수상 타자는 **{actual_info['선수명']}**입니다."
        )

# 7. 전체 리더보드 (순위표)
st.subheader(f"📋 {selected_year}시즌 전체 타자 MVP 점수 순위표")

display_cols = ["선수명", "팀", "타석", "타율", "출루율", "장타율", "OPS", "MVP점수"]
df_display = df_year[display_cols].copy()
df_display.index = df_display.index + 1  # 1위부터 시작하도록 인덱스 조정
df_display.columns = [
    "선수명",
    "팀",
    "타석",
    "타율",
    "출루율",
    "장타율",
    "OPS",
    "MVP 점수",
]

st.dataframe(
    df_display.style.format(
        {
            "타율": "{:.3f}",
            "출루율": "{:.3f}",
            "장타율": "{:.3f}",
            "OPS": "{:.3f}",
            "MVP 점수": "{:.4f}",
            "타석": "{:.0f}",
        }
    ),
    use_container_width=True,
)
