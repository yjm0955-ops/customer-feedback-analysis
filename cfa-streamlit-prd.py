import streamlit as st
import pandas as pd
# from textblob import TextBlob # TextBlob is less effective for Korean
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import re
import matplotlib.font_manager as fm
from konlpy.tag import Okt

# Initialize Konlpy Okt tagger
okt = Okt()

# Define simple Korean sentiment lexicon (can be expanded)
sentiment_lexicon = {
    '긍정': ['만족', '좋', '최고', '추천', '감사', '훌륭', '편리', '신선', '맛있', '친절', '빠르'],
    '부정': ['불만', '나쁘', '아쉽', '별로', '문제', '느리', '작', '크', '어렵', '수축', '부족', '기대이하', '비싸']
}

# For Korean font in matplotlib
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf' # Linux (adjust as needed)
# font_path = 'C:/Windows/Fonts/malgun.ttf' # Windows

try:
    # Clear font cache to ensure new font is loaded
    fm._load_fontmanager(try_read_cache=False)
    
    # Add the font file to FontManager (if not already added)
    if font_path not in [f.fname for f in fm.fontManager.ttflist]:
        fm.fontManager.addfont(font_path)
    
    # Set the font family to the known font name
    plt.rcParams['font.family'] = 'NanumGothic' # Use the exact font name
    plt.rcParams['axes.unicode_minus'] = False # minus sign
    st.success(f"'NanumGothic' 폰트가 성공적으로 설정되었습니다.")
except FileNotFoundError:
    st.error(f"'{font_path}' 폰트 파일을 찾을 수 없습니다. 그래프에 한글이 깨져 보일 수 있습니다. 경로를 확인하거나 다른 한글 폰트를 설정해주세요.")
    st.stop() # Stop the app if font file is not found
except Exception as e:
    st.error(f"폰트 설정 중 오류가 발생했습니다: {e}. 그래프에 한글이 깨져 보일 수 있습니다.")
    st.info("만약 Linux 환경이라면, /usr/share/fonts/truetype/nanum/NanumGothic.ttf 경로를 확인하거나, 해당 경로에 NanumGothic 폰트를 설치해주세요.")
    st.stop() # Stop the app if other font errors occur

# Set page configuration
st.set_page_config(layout="wide", page_title="고객 피드백 분석 앱", page_icon="💬")

st.title("💬 고객 피드백 분석 (Streamlit 버전)")
st.markdown("---")

st.sidebar.header("데이터 선택")
use_sample_data = st.sidebar.checkbox("샘플 데이터 사용 (feedback-data.csv)")

df = None
if use_sample_data:
    try:
        df = pd.read_csv('feedback-data.csv')
        st.sidebar.success("샘플 데이터 로드 성공!")
        st.sidebar.write("데이터 미리보기:")
        st.sidebar.dataframe(df.head())
    except FileNotFoundError:
        st.sidebar.error("'feedback-data.csv' 파일을 찾을 수 없습니다. 샘플 데이터를 먼저 생성해주세요.")
        st.stop()
    except Exception as e:
        st.sidebar.error(f"샘플 데이터 로드 중 오류 발생: {e}")
        st.stop()
else:
    uploaded_file = st.sidebar.file_uploader("CSV 또는 Excel 파일 업로드", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.sidebar.success("파일 업로드 성공!")
            st.sidebar.write("데이터 미리보기:")
            st.sidebar.dataframe(df.head())
        except Exception as e:
            st.sidebar.error(f"파일 처리 중 오류가 발생했습니다: {e}")
            st.sidebar.warning("파일 형식이나 내용이 올바른지 확인해주세요.")


if df is not None:
    # Select text column
    text_column = st.sidebar.selectbox("피드백 텍스트 컬럼 선택", df.columns)
    if text_column:
        st.subheader("데이터 분석 시작")
        st.write(f"선택된 텍스트 컬럼: **{text_column}**")

        # --- 감성 분석 ---
        st.subheader("1. 감성 분석")

        @st.cache_data
        def analyze_sentiment_korean(text):
            if pd.isna(text) or not isinstance(text, str):
                return "중립", 0.0
            
            score = 0
            words = okt.morphs(text, stem=True) # 형태소 분석 및 어간 추출
            
            for word in words:
                if any(pos_word in word for pos_word in sentiment_lexicon['긍정']):
                    score += 1
                if any(neg_word in word for neg_word in sentiment_lexicon['부정']):
                    score -= 1

            if score > 0:
                return "긍정", score
            elif score < 0:
                return "부정", score
            else:
                return "중립", score

        # Use Korean sentiment analysis function
        df[['감성', '감성_점수']] = df[text_column].apply(lambda x: pd.Series(analyze_sentiment_korean(x)))

        sentiment_counts = df['감성'].value_counts()
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        sentiment_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, ax=ax1,
                              colors=['#66b3ff', '#ff9999', '#99ff99'])
        ax1.set_ylabel('')
        ax1.set_title('전체 피드백 감성 분포')
        st.pyplot(fig1)

        st.dataframe(df[['감성', '감성_점수', text_column]].head())

        # --- 키워드 추출 ---
        st.subheader("2. 주요 키워드 추출")

        @st.cache_data
        def extract_keywords_korean(text_series):
            all_nouns = []
            for text in text_series.dropna():
                # 명사만 추출
                nouns = okt.nouns(text)
                all_nouns.extend(nouns)
            return Counter(all_nouns)

        word_counts = extract_keywords_korean(df[text_column])

        st.write("가장 많이 언급된 키워드 (상위 20개):")
        most_common_words = pd.DataFrame(word_counts.most_common(20), columns=['키워드', '빈도'])
        fig2, ax2 = plt.subplots(figsize=(12, 7))
        sns.barplot(x='빈도', y='키워드', data=most_common_words, ax=ax2, palette='viridis')
        ax2.set_title('주요 키워드 빈도')
        ax2.set_xlabel('빈도')
        ax2.set_ylabel('키워드')
        st.pyplot(fig2)

        # --- 상세 필터링 및 분석 ---
        st.subheader("3. 상세 분석 (필터링)")
        st.markdown("---")

        st.write("감성별 주요 키워드를 확인하거나, 특정 키워드를 포함하는 피드백을 필터링할 수 있습니다.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("감성별 키워드")
            selected_sentiment = st.radio("확인할 감성 선택", ['긍정', '부정', '중립'])
            filtered_sentiment_df = df[df['감성'] == selected_sentiment]
            sentiment_word_counts = extract_keywords_korean(filtered_sentiment_df[text_column])
            if sentiment_word_counts:
                most_common_sentiment_words = pd.DataFrame(sentiment_word_counts.most_common(10), columns=['키워드', '빈도'])
                st.dataframe(most_common_sentiment_words)
            else:
                st.write(f"'{selected_sentiment}' 감성 피드백이 없습니다.")

        with col2:
            st.subheader("키워드로 피드백 검색")
            search_keyword = st.text_input("검색할 키워드를 입력하세요 (예: '배송', '품질')")
            if search_keyword:
                filtered_by_keyword_df = df[df[text_column].astype(str).str.contains(search_keyword, case=False, na=False)]
                if not filtered_by_keyword_df.empty:
                    st.write(f"'{search_keyword}'(을)를 포함하는 피드백:")
                    st.dataframe(filtered_by_keyword_df[[text_column, '감성', '감성_점수']])
                else:
                    st.write(f"'{search_keyword}'(을)를 포함하는 피드백이 없습니다.")
            else:
                st.write("키워드를 입력하여 관련 피드백을 찾아보세요.")

else:
    st.info("왼쪽 사이드바에서 파일을 업로드하거나 샘플 데이터를 사용하세요.")

st.info("한글 감성 분석은 konlpy 라이브러리를 사용하며, 정의된 긍정/부정 키워드를 기반으로 분류됩니다. 키워드 사전은 확장할 수 있습니다.")
