import pandas as pd  # 표 형태 데이터를 다루는 라이브러리

# CSV 파일 불러오기 (이 파일과 같은 폴더에 있는 sales_sample.csv)
df = pd.read_csv("sales_sample.csv")

# 1) 행·열 개수: shape는 (행 개수, 열 개수)를 알려 준다
print("=== 1. 행·열 개수 ===")
print(f"행: {df.shape[0]}개, 열: {df.shape[1]}개")
print()

# 2) 열 이름과 자료형: dtypes는 열마다 어떤 종류의 값인지 알려 준다
#    (int64=정수, float64=소수, str=글자 / 예전 pandas에서는 글자가 object로 보인다)
print("=== 2. 열 이름과 자료형 ===")
print(df.dtypes)
print()

# 3) 빈칸 개수: isna()로 빈칸을 찾고 sum()으로 열마다 개수를 센다
print("=== 3. 빈칸 개수 ===")
print(df.isna().sum())
print()

# 4) 숫자 열 요약: describe()는 개수, 평균, 표준편차, 최솟값, 사분위수, 최댓값을 보여 준다
print("=== 4. 숫자 열 요약 ===")
print(df.describe())
print()

# 5) 조건으로 골라내기: 서울 지역이면서 매출이 10만 원 이상인 주문
print("=== 5. 서울 & 매출 10만 원 이상 주문 ===")
is_seoul = df["region"] == "서울"        # 지역이 '서울'인지 행마다 True/False로 표시
is_big = df["sales"] >= 100000           # 매출이 10만 원 이상인지 행마다 True/False로 표시
seoul_big = df[is_seoul & is_big]        # 두 조건이 모두 True인 행만 골라 새 표로 만든다
print(f"{len(seoul_big)}건")             # len()으로 골라낸 행 개수를 센다
print()

# 6) 지역별 매출 합계를 큰 순서로
print("=== 6. 지역별 매출 합계 (큰 순서) ===")
region_sales = df.groupby("region")["sales"].sum()             # 지역별로 묶어서 매출을 더한다
region_sales = region_sales.sort_values(ascending=False)       # ascending=False → 큰 값부터 정렬
for region, total in region_sales.items():                     # 지역 이름과 합계를 하나씩 꺼낸다
    print(f"{region}: {total:,}원")                            # :, → 천 단위 쉼표를 찍는다
print()

# ----- 화면(app.py)에 보여 줄 집계 2개 -----

# 7) 월별 매출 합계 (1월 → 10월 순서)
print("=== 7. 월별 매출 합계 ===")
df["date"] = pd.to_datetime(df["date"])                        # 글자로 된 날짜를 날짜 형식으로 바꾼다
df["month"] = df["date"].dt.month                              # 날짜에서 '월' 숫자만 꺼내 새 열로 만든다
month_sales = df.groupby("month")["sales"].sum()               # 월별로 묶어서 매출을 더한다 (월 순서로 정렬됨)
for month, total in month_sales.items():
    print(f"{month}월: {total:,}원")
print()

# 8) 카테고리별 매출 합계 (큰 순서)
print("=== 8. 카테고리별 매출 합계 (큰 순서) ===")
category_sales = df.groupby("category")["sales"].sum().sort_values(ascending=False)  # 묶고 → 더하고 → 큰 값부터
for category, total in category_sales.items():
    print(f"{category}: {total:,}원")
print()

# ----- 연습: 한 줄로 쓰는 pandas 질문 3개 -----
# (date 열은 7번에서 이미 날짜 형식으로 바꿨기 때문에 .dt.month를 쓸 수 있다)

# 9) 부산 매출 합계: 부산 행만 고르고 → sales 열을 → 더한다
print("=== 9. 부산 매출 합계 ===")
print(df[df["region"] == "부산"]["sales"].sum())
print()

# 10) 카테고리별 평균 매출: 카테고리로 묶고 → sales 평균 → 큰 순서로 정렬
print("=== 10. 카테고리별 평균 매출 (큰 순서) ===")
print(df.groupby("category")["sales"].mean().sort_values(ascending=False))
print()

# 11) 3월이면서 매출 20만 원 이상인 주문 수: 두 조건을 각각 괄호로 감싸고 &로 묶는다
print("=== 11. 3월 & 매출 20만 원 이상 주문 수 ===")
print(len(df[(df["date"].dt.month == 3) & (df["sales"] >= 200000)]))
