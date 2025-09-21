
import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px
import re

st.set_page_config(layout="wide")

def get_sentiment(text):
    # 간단한 키워드 기반 감성 분석 (확장을 위해 함수로 분리)
    negative_keywords = ["아쉽", "별로", "나쁘", "문제", "어렵", "불친절", "버그", "최악", "돈이 아깝"]
    positive_keywords = ["만족", "좋", "친절", "빠르", "신속", "감사", "추천", "완벽"]

    text_lower = text.lower()

    for keyword in negative_keywords:
        if keyword in text_lower:
            return "부정"
    for keyword in positive_keywords:
        if keyword in text_lower:
            return "긍정"
    return "중립"

def extract_keywords(text):
    # 간단한 키워드 추출 (불용어 제거 및 명사 위주)
    text = re.sub(r'[^\w\s]', '', text)  # 특수문자 제거
    words = [word for word in text.split() if len(word) > 1] # 한 글자 단어 제외
    return words

st.title("고객 피드백 분석 앱")
st.markdown("--- ")

# 파일 업로드
uploaded_file = st.sidebar.file_uploader("피드백 데이터 파일 업로드 (CSV)", type=["csv"])

st.sidebar.markdown("--- ")
use_sample_data = st.sidebar.checkbox("샘플 데이터 (@feedback-data.csv) 사용")

df = None
if use_sample_data:
    try:
        df = pd.read_csv("@feedback-data.csv")
        st.sidebar.success("샘플 데이터가 로드되었습니다.")
    except FileNotFoundError:
        st.sidebar.error("'@feedback-data.csv' 파일을 찾을 수 없습니다. 프로젝트 폴더에 파일이 있는지 확인하세요.")
    except Exception as e:
        st.sidebar.error(f"샘플 데이터 로드 중 오류가 발생했습니다: {e}")
elif uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("파일이 성공적으로 업로드되었습니다.")
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# df가 성공적으로 로드되었을 경우에만 분석 및 시각화 진행
if df is not None:
    # 필요한 컬럼 확인 (샘플 데이터도 이 검증을 통과해야 함)
    required_columns = ["date", "product", "feedback_text", "rating"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"업로드된 파일에 필요한 컬럼({', '.join(required_columns)})이 모두 포함되어 있지 않습니다.")
        df = None # 컬럼이 부족하면 df를 None으로 설정하여 아래 분석 로직 실행 방지
    else:
        # 날짜 컬럼을 datetime으로 변환
        df["date"] = pd.to_datetime(df["date"])
        st.write("### 원본 데이터 미리보기")
        st.dataframe(df.head())

        # 감성 분석 및 키워드 추출
        st.write("### 데이터 분석 중...")
        df["sentiment"] = df["feedback_text"].apply(get_sentiment)
        
        all_keywords = []
        for text in df["feedback_text"]:
            all_keywords.extend(extract_keywords(text))
        
        st.success("분석 완료!")

        st.markdown("--- ")
        st.write("### 분석 결과")

        # 감성 분포 시각화
        st.write("#### 감성 분포")
        sentiment_counts = df["sentiment"].value_counts().reset_index()
        sentiment_counts.columns = ["Sentiment", "Count"]
        fig_sentiment = px.pie(sentiment_counts, values="Count", names="Sentiment", title="고객 피드백 감성 분포")
        st.plotly_chart(fig_sentiment, use_container_width=True)

        # 키워드 빈도 시각화
        st.write("#### 주요 키워드")
        keyword_counts = Counter(all_keywords).most_common(20) # 상위 20개 키워드
        keyword_df = pd.DataFrame(keyword_counts, columns=["Keyword", "Count"])
        fig_keywords = px.bar(keyword_df, x="Keyword", y="Count", title="주요 키워드 빈도", color="Count")
        st.plotly_chart(fig_keywords, use_container_width=True)

        # 제품별 감성 분석 (선택 박스)
        st.write("#### 제품별 감성 분석")
        selected_product = st.selectbox("제품을 선택하세요", ["All"] + list(df["product"].unique()))

        if selected_product != "All":
            product_df = df[df["product"] == selected_product]
            product_sentiment_counts = product_df["sentiment"].value_counts().reset_index()
            product_sentiment_counts.columns = ["Sentiment", "Count"]
            fig_product_sentiment = px.pie(product_sentiment_counts, values="Count", names="Sentiment", title=f"{selected_product} 감성 분포")
            st.plotly_chart(fig_product_sentiment, use_container_width=True)
        else:
            st.write("전체 제품의 감성 분포는 위에 표시되어 있습니다.")

else:
    st.info("왼쪽 사이드바에서 CSV 파일을 업로드하거나 샘플 데이터를 선택하여 분석을 시작하세요.")
