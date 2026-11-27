import streamlit as st  # 웹 화면을 만드는 라이브러리
import pandas as pd     # 표 형태 데이터를 다루는 라이브러리

# 페이지 설정: 브라우저 탭 제목과 넓은 화면(wide) 레이아웃
st.set_page_config(page_title="매출 현황", layout="wide")


DATA_FILE = "sales_sample.csv"                                      # 불러올 데이터 파일 이름
REQUIRED_COLUMNS = ["date", "region", "category", "sales", "quantity"]  # 화면에 꼭 필요한 열


# 데이터 불러오기 함수
# @st.cache_data: 처음 한 번만 파일을 읽고 결과를 저장(캐시)해 둔다.
# 사이드바 조건을 바꿔 화면이 다시 그려져도 파일을 또 읽지 않고 저장된 결과를 쓴다.
@st.cache_data
def load_data(path):
    return pd.read_csv(path)  # 날짜 변환은 열이 있는지 확인한 뒤에 따로 한다


# 화면 맨 위 제목과 캡션(작은 설명 글) — 데이터에 문제가 있어도 제목은 먼저 보이도록 위로 올렸다
st.title("영업팀 매출 현황")
st.caption("영업팀장이 지역·카테고리·기간을 고르면 매출 추이와 지역별 실적을 볼 수 있는 화면 · 데이터 기준: 2026년 1~10월 · 출처: sales_sample.csv")

# ===== 안전장치 1: 파일 읽기 =====
# try: 일단 해 보고, except: 문제가 생기면 빨간 에러 대신 안내를 보여 준다
try:
    raw = load_data(DATA_FILE)
except FileNotFoundError:   # 파일이 없을 때
    st.error(
        f"데이터 파일 '{DATA_FILE}'을(를) 찾을 수 없습니다. "
        f"파일 이름이 정확한지, app.py와 같은 폴더에 있는지 확인해 주세요."
    )
    st.stop()               # 여기서 멈추고 아래 코드는 실행하지 않는다
except Exception:           # 파일은 있지만 비어 있거나 CSV 형식이 아닐 때
    st.error(
        f"데이터 파일 '{DATA_FILE}'을(를) 읽을 수 없습니다. "
        f"파일이 비어 있지 않은지, 쉼표로 구분된 CSV 형식인지 확인해 주세요."
    )
    st.stop()

# ===== 안전장치 2: 필요한 열이 모두 있는지 =====
missing = [col for col in REQUIRED_COLUMNS if col not in raw.columns]  # 없는 열만 모은 목록
if missing:
    st.error(
        f"데이터 파일에 꼭 필요한 열이 없습니다: {', '.join(missing)}. "
        f"파일 첫 줄의 열 이름이 {', '.join(REQUIRED_COLUMNS)}인지 확인해 주세요."
    )
    st.stop()

# ===== 안전장치 3: 값이 잘못된 행 빼기 =====
df = raw.copy()                                                   # 캐시된 원본은 건드리지 않도록 복사본을 쓴다
df["date"] = pd.to_datetime(df["date"], errors="coerce")          # 날짜로 못 바꾸는 값은 빈칸(NaT)으로
df["sales"] = pd.to_numeric(df["sales"], errors="coerce")         # 숫자로 못 바꾸는 값은 빈칸(NaN)으로
bad_rows = df["date"].isna() | df["sales"].isna()                 # 날짜나 매출이 빈칸인 행
if bad_rows.any():
    df = df[~bad_rows]                                            # ~는 '반대' → 잘못된 행을 뺀 나머지
    st.warning(
        f"날짜나 매출 값이 비었거나 잘못된 {bad_rows.sum()}행은 빼고 보여 줍니다. "
        f"정확한 결과가 필요하면 원본 파일에서 해당 행을 고쳐 주세요."
    )
if df.empty:
    st.error("데이터 파일에 쓸 수 있는 행이 하나도 없습니다. 파일에 날짜와 매출 값이 들어 있는지 확인해 주세요.")
    st.stop()

# ===== 왼쪽 사이드바: 조건 선택 =====
st.sidebar.header("조건 선택")

# 1) 지역: 여러 개 선택 가능, 처음에는 전체 지역이 선택된 상태
all_regions = sorted(df["region"].unique())          # 데이터에 있는 지역 목록 (가나다순)
selected_regions = st.sidebar.multiselect(
    "지역", options=all_regions, default=all_regions  # default=전체 → 처음엔 모두 선택
)

# 2) 카테고리: 드롭다운, 맨 앞에 '전체'를 넣는다
category_options = ["전체"] + sorted(df["category"].unique())
selected_category = st.sidebar.selectbox("카테고리", options=category_options)

# 3) 기간: 시작일~종료일을 고르는 슬라이더
min_date = df["date"].min().date()   # 데이터의 첫 날짜 (.date()로 시간 부분을 뺀다)
max_date = df["date"].max().date()   # 데이터의 마지막 날짜
if min_date == max_date:             # 날짜가 하루뿐이면 슬라이더를 만들 수 없어서(에러) 글로만 보여 준다
    start_date, end_date = min_date, max_date
    st.sidebar.caption(f"기간: {min_date} (하루치 데이터)")
else:
    start_date, end_date = st.sidebar.slider(
        "기간",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),  # 값을 2개 주면 '범위' 슬라이더가 된다 (처음엔 전체 기간)
        format="YYYY-MM-DD",
    )

# ===== 조건으로 데이터 걸러내기 → filtered =====
is_region = df["region"].isin(selected_regions)                  # 선택한 지역 목록 안에 있으면 True
if selected_category == "전체":
    is_category = pd.Series(True, index=df.index)                # '전체'면 모든 행을 True로
else:
    is_category = df["category"] == selected_category            # 고른 카테고리와 같으면 True
is_period = df["date"].dt.date.between(start_date, end_date)     # 시작일~종료일 사이면 True (양 끝 포함)

filtered = df[is_region & is_category & is_period]               # 세 조건을 모두 만족하는 행만 남긴다

# 필터 아래에 몇 건이 골라졌는지 표시
st.sidebar.markdown(f"**선택 조건: {len(filtered):,}건 / 전체 {len(df):,}건**")

# ===== 안전장치 4: 조건에 맞는 데이터가 0건일 때 =====
# 안내만 보여 주고 멈춘다 → 지표·그래프·표는 그리지 않는다
# (멈추지 않으면 평균 주문액 계산에서 0으로 나누는 문제가 생긴다)
if filtered.empty:
    st.info(
        "선택한 조건에 맞는 주문이 0건입니다. "
        "사이드바에서 지역을 더 고르거나, 카테고리를 '전체'로 바꾸거나, 기간을 늘려서 조건을 넓혀 보세요."
    )
    st.stop()

# ===== 본문 탭 두 개 =====
tab_summary, tab_detail = st.tabs(["요약", "상세 데이터"])

with tab_summary:
    # 핵심 지표 3개 계산
    total_sales = filtered["sales"].sum()    # 총 매출: sales 열을 모두 더한다
    order_count = len(filtered)              # 주문 건수: 행 개수 = 주문 개수
    avg_order = total_sales / order_count    # 평균 주문액: 총 매출 ÷ 주문 건수

    # 화면을 가로로 3칸 나눠서 지표를 하나씩 넣는다
    col1, col2, col3 = st.columns(3)
    col1.metric("총 매출", f"{total_sales:,.0f}원")      # :, → 천 단위 쉼표, .0f → 소수점 없이
    col2.metric("주문 건수", f"{order_count:,}건")
    col3.metric("평균 주문액", f"{avg_order:,.0f}원")    # .0f → 소수점 없이 반올림

    # ----- 그래프 1: 월별 매출 추이 (선 그래프) -----
    st.subheader("월별 매출 추이")
    month = filtered["date"].dt.strftime("%Y-%m").rename("month")      # 날짜를 '2026-01' 같은 글자로 바꾼다 (두 자리라 순서가 맞다)
    month_sales = filtered.groupby(month)["sales"].sum().reset_index()  # 월별 합계 → reset_index()로 month를 보통 열로 꺼낸다
    st.line_chart(month_sales, x="month", y="sales", x_label="월", y_label="매출(원)")

    # ----- 그래프 2: 지역별 매출 (막대 그래프, 큰 순서) -----
    st.subheader("지역별 매출")
    region_sales = filtered.groupby("region")["sales"].sum().reset_index()  # 지역별 합계
    st.bar_chart(
        region_sales, x="region", y="sales", x_label="지역", y_label="매출(원)",
        sort="-sales",  # sales 기준 정렬, 앞의 '-'는 큰 값부터(내림차순)라는 뜻
    )

    # ----- 경영 판단: 선택한 조건에 따라 1위 지역·최고 매출 달이 바뀐다 -----
    st.subheader("이 화면으로 내릴 수 있는 경영 판단")
    top_region = region_sales.loc[region_sales["sales"].idxmax()]   # idxmax(): 매출이 가장 큰 행의 위치 → 그 행을 꺼낸다
    top_month = month_sales.loc[month_sales["sales"].idxmax()]      # 월별 표에서도 같은 방법으로 1위 달을 꺼낸다
    region_share = top_region["sales"] / total_sales * 100          # 1위 지역이 선택 조건 매출에서 차지하는 비율(%)
    month_label = f"{top_month['month'][:4]}년 {int(top_month['month'][5:])}월"  # '2026-04' → '2026년 4월'

    if len(region_sales) == 1:   # 지역을 하나만 골랐으면 '1위'·'우선 배치'라는 말이 어색해서 문장을 바꾼다
        region_text = f"선택한 **{top_region['region']}** 지역의 매출은 {top_region['sales']:,.0f}원이고"
        action_text = ""
    else:
        region_text = (
            f"선택한 조건에서 매출 1위 지역은 **{top_region['region']}**"
            f"({top_region['sales']:,.0f}원, {region_share:.0f}%)이고"
        )
        action_text = f"**{top_region['region']}** 지역에 영업 자원을 우선 배치하고, "
    st.info(
        f"{region_text}, 매출이 가장 높은 달은 **{month_label}**({top_month['sales']:,.0f}원)입니다. "
        f"{action_text}**{month_label}**에 매출이 높았던 이유를 찾아 다른 달의 영업 계획에 반영하는 것을 검토할 수 있습니다."
    )

with tab_detail:
    st.dataframe(
        filtered,
        width="stretch",   # 표를 화면 폭에 꽉 맞춘다
        hide_index=True,   # 왼쪽 행 번호(0, 1, 2…)를 숨긴다
        column_config={
            "date": st.column_config.DateColumn(format="YYYY-MM-DD"),  # 날짜 뒤의 '00:00:00' 시간 표시를 없앤다
        },
    )
