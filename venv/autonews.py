from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import openai

# 요청하고자 하는 샘플 뉴스기사 URL
url = 'https://www.investing.com/analysis/us-stock-market-has-plenty-of-reasons-to-rally-after-feds-decision-200634857'

# 크롬드라이버 셋팅
def set_chrome_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('headless')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def summarize(prompt):
    # 모델 엔진 선택
    model_engine = "text-davinci-003"

    # 맥스 토큰
    max_tokens = 3000

    # 요약 요청
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=0.3,       # creativity
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return completion

# driver 설정
driver = set_chrome_driver(False)

# URL 요청
driver.get(url)

# aritivlePage는 신문기사의 본문입니다
article_page = driver.find_element(By.CLASS_NAME, 'articlePage')
article_page
#print(article_page.text)

# API 키 설정
openai.api_key = "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"

# 프롬프트 (요약해줘 + 긍/부정 감정도 분석해줘)
prompt = f'''
Summarize the paragraph below and interpret whether it is a positive or negative sentiment.

{article_page.text}
'''
#print(prompt)


# 요약 요청후 결과 return
response = summarize(prompt)

# 결과 출력
print(response.choices[0].text)