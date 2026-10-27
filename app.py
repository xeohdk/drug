import numpy as np
import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------
# 1. 계산 및 외부 API 연동 함수
# ---------------------------------------------------------
def calculate_remaining(initial_amount, half_life, elapsed_time):
    """일차 제거 모델에 따른 잔존량(mg)을 계산한다."""
    return initial_amount * np.power(0.5, elapsed_time / half_life)


def recommend_dosing_interval(half_life):
    """반감기를 바탕으로 학술적 기준의 권장 복용 간격 범위(시간)를 산출한다."""
    return half_life, half_life * 2.0


@st.cache_data
def fetch_drug_from_pubchem(ingredient_name):
    """PubChem REST API를 통해 약물 성분 정보를 검색한다."""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/property/Title,MolecularWeight/JSON"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            properties = data["PropertyTable"]["Properties"][0]
            return {
                "success": True,
                "name": properties.get("Title", ingredient_name),
                "molecular_weight": properties.get("MolecularWeight", 0.0),
            }
        return {"success": False, "message": "API에서 해당 약물 정보를 찾을 수 없습니다."}
    except Exception as e:
        return {"success": False, "message": f"API 통신 오류: {str(e)}"}


# 대표 성분별 평균 반감기 및 기본 용량 매핑 DB
KNOWN_HALF_LIVES = {
    "Acetaminophen": {"half_life": 2.0, "default_dose": 500.0, "kr_name": "아세트아미노펜 (타이레놀)"},
    "Ibuprofen": {"half_life": 2.0, "default_dose": 200.0, "kr_name": "이부프로펜 (부루펜)"},
    "Caffeine": {"half_life": 5.0, "default_dose": 100.0, "kr_name": "카페인"},
    "Aspirin": {"half_life": 0.25, "default_dose": 500.0, "kr_name": "아스피린"},
}


# ---------------------------------------------------------
# 2. 페이지 설정 및 기본 안내
# ---------------------------------------------------------
st.set_page_config(
    page_title="가상 약물 잔존량 학습 시뮬레이터",
    layout="centered"
)

st.title("가상 약물 잔존량 학습 시뮬레이터")
st.warning(
    "가상의 조건을 이용하는 교육용 프로그램입니다. "
    "실제 복용량, 복용 간격, 약효 또는 안전성을 판단할 수 없습니다."
)
st.write(
    "초기량과 반감기를 바꾸며 시간에 따른 잔존량을 확인하세요. "
    "초기 시점에 약물이 이미 체내에 있고, 일정한 반감기로 제거된다고 가정합니다."
)


# ---------------------------------------------------------
# 3. 약물 조건 설정 (API 및 프리셋)
# ---------------------------------------------------------
st.subheader("1. 약물 조건 선택")
search_type = st.radio("입력 방식 선택", ["자주 쓰는 성분 선택", "PubChem API 직접 검색", "수동 숫자 입력"])

selected_half_life = 4.0
selected_dose = 100.0

if search_type == "자주 쓰는 성분 선택":
    selected_key = st.selectbox(
        "성분을 선택하세요",
        options=list(KNOWN_HALF_LIVES.keys()),
        format_func=lambda x: f"{KNOWN_HALF_LIVES[x]['kr_name']} ({x})"
    )
    info = KNOWN_HALF_LIVES[selected_key]
    selected_half_life = info["half_life"]
    selected_dose = info["default_dose"]
    st.info(f"선택 성분: **{info['kr_name']}** | 평균 반감기: 약 **{selected_half_life}시간**")

elif search_type == "PubChem API 직접 검색":
    ingredient_input = st.text_input("성분 영문명 입력 (예: Acetaminophen, Caffeine, Ibuprofen)", "Acetaminophen")
    if ingredient_input:
        api_result = fetch_drug_from_pubchem(ingredient_input)
        if api_result["success"]:
            st.success(f"API 조회 성공: **{api_result['name']}** (분자량: {api_result['molecular_weight']})")
            
            matched_key = next((k for k in KNOWN_HALF_LIVES if k.lower() == ingredient_input.strip().lower()), None)
            if matched_key:
                selected_half_life = KNOWN_HALF_LIVES[matched_key]["half_life"]
                selected_dose = KNOWN_HALF_LIVES[matched_key]["default_dose"]
                st.info(f"매핑된 평균 반감기({selected_half_life}시간) 및 기본 용량({selected_dose}mg)을 불어왔습니다.")
            else:
                st.warning("화학 정보 조회가 완료되었으나 반감기 자동 매칭 데이터가 없으므로 아래 폼에서 반감기를 조정해 주세요.")
        else:
            st.error(api_result["message"])


# ---------------------------------------------------------
# 4. 시뮬레이션 입력 폼
# ---------------------------------------------------------
st.subheader("2. 시뮬레이션 수치 입력")
with st.form("simulation_form"):
    initial_amount = st.number_input(
        "초기량 (mg)",
        min_value=0.0,
        max_value=10000.0,
        value=float(selected_dose),
        step=10.0,
        format="%.2f"
    )
    half_life = st.number_input(
        "반감기 (시간)",
        min_value=0.0,
        max_value=1000.0,
        value=float(selected_half_life),
        step=0.5,
        format="%.2f"
    )
    duration = st.number_input(
        "관찰 시간 (시간)",
        min_value=0.0,
        max_value=1000.0
