import numpy as np
import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------
# 1. 오픈 API 연동 및 약동학(PK) 데이터베이스
# ---------------------------------------------------------
@st.cache_data
def search_pubchem_compound(ingredient_name):
    """
    PubChem Open API를 호출하여 입력받은 성분의 화학 정보 및 분자량을 가져옵니다.
    """
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/property/Title,MolecularWeight,IUPACName/JSON"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            props = data["PropertyTable"]["Properties"][0]
            return {
                "success": True,
                "cid": props.get("CID"),
                "title": props.get("Title", ingredient_name),
                "molecular_weight": props.get("MolecularWeight", 0.0),
                "iupac_name": props.get("IUPACName", "-")
            }
        return {"success": False, "message": "API에서 해당 성분을 찾지 못했습니다."}
    except Exception as e:
        return {"success": False, "message": f"API 통신 오류: {str(e)}"}


# 실제 주요 의약품 성분별 의약학 표준 반감기 및 용량 데이터베이스 (확장 가능)
REAL_DRUG_PK_DATABASE = {
    "acetaminophen": {
        "kr_name": "아세트아미노펜 (타이레놀)",
        "half_life": 2.0,
        "standard_dose": 500.0,
        "category": "해열진통제",
        "description": "간에서 주로 대사되며, 성인 기준 평균 반감기는 약 2시간입니다."
    },
    "ibuprofen": {
        "kr_name": "이부프로펜 (부루펜/이지엔6)",
        "half_life": 2.1,
        "standard_dose": 200.0,
        "category": "소염진통제",
        "description": "신장 및 간을 통해 배설되며, 반감기는 약 2~2.5시간입니다."
    },
    "caffeine": {
        "kr_name": "카페인 (Caffeine)",
        "half_life": 5.0,
        "standard_dose": 100.0,
        "category": "중추신경흥분제",
        "description": "성인 기준 평균 3~7시간(평균 5시간)의 반감기를 가집니다."
    },
    "aspirin": {
        "kr_name": "아스피린 (Aspirin)",
        "half_life": 0.25,
        "standard_dose": 500.0,
        "category": "항혈소판제/진통제",
        "description": "체내에서 살리실산으로 급속히 가수분해되며 초기 반감기는 약 15분입니다."
    },
    "amoxicillin": {
        "kr_name": "아목시실린 (항생제)",
        "half_life": 1.0,
        "standard_dose": 250.0,
        "category": "페니실린계 항생제",
        "description": "주로 신장을 통해 배설되며 반감기는 약 1시간 내외입니다."
    },
    "loratadine": {
        "kr_name": "로라타딘 (클라리틴)",
        "half_life": 10.0,
        "standard_dose": 10.0,
        "category": "항히스타민제",
        "description": "2세대 항히스타민제로 약 8~11시간의 반감기를 가집니다."
    }
}


# ---------------------------------------------------------
# 2. 계산 모델 함수
# ---------------------------------------------------------
def calculate_single_dose(initial_amount, half_life, times):
    """단회 투여 시 잔존량 계산 식: A(t) = A0 * (1/2)^(t / T)"""
    return initial_amount * np.power(0.5, times / half_life)


def calculate_multiple_doses(dose_amount, half_life, interval, total_hours):
    """다회 정기 복용 시 체내 누적 및 제거 시뮬레이션 계산 함수"""
    times = np.linspace(0, total_hours, int(total_hours * 10) + 1)
    amounts = np.zeros_like(times)
    
    for i, t in enumerate(times):
        # 복용 횟수 계산
        num_doses = int(t // interval) + 1
        current_amount = 0.0
        for d in range(num_doses):
            dose_time = d * interval
            if t >= dose_time:
                elapsed = t - dose_time
                current_amount += dose_amount * (0.5 ** (elapsed / half_life))
        amounts[i] = current_amount
        
    return times, amounts


# ---------------------------------------------------------
# 3. UI 및 시뮬레이터 구현
# ---------------------------------------------------------
st.set_page_config(page_title="실제 약물 오픈 API 반감기 시뮬레이터", layout="wide")

st.title("💊 실제 약물 Open API 기반 반감기 계산 시뮬레이터")
st.caption("PubChem API 화학 정보 검색 및 약동학(PK) 데이터베이스를 결합한 약물 잔존량 시각화 모델")

st.warning(
    "⚠️ **주의**: 본 프로그램은 오픈 API와 일차 제거 수학 모델을 활용한 교육·연구용 시뮬레이터입니다. "
    "실제 환자의 복용법 변경이나 의학적 의사결정의 근거로 사용할 수 없습니다."
)

# Sidebar - 검색 및 설정
st.sidebar.header("🔍 1. 약물 검색 (Open API)")
search_mode = st.sidebar.radio("검색 방식", ["등록된 약물 성분 선택", "PubChem API 성분 직접 검색"])

selected_half_life = 2.0
selected_dose = 500.0
drug_display_name = "아세트아미노펜"

if search_mode == "등록된 약물 성분 선택":
    drug_key = st.sidebar.selectbox(
        "약물 성분 선택",
        options=list(REAL_DRUG_PK_DATABASE.keys()),
        format_func=lambda x: REAL_DRUG_PK_DATABASE[x]["kr_name"]
    )
    pk_info = REAL_DRUG_PK_DATABASE[drug_key]
    selected_half_life = pk_info["half_life"]
    selected_dose = pk_info["standard_dose"]
    drug_display_name = pk_info["kr_name"]
    
    st.sidebar.success(f"**분류**: {pk_info['category']}")
    st.sidebar.info(pk_info['description'])

else:
    user_query = st.sidebar.text_input("영문 성분명 입력 (예: Acetaminophen, Ibuprofen)", "Acetaminophen")
    if user_query:
        api_res = search_pubchem_compound(user_query.strip())
        if api_res["success"]:
            st.sidebar.success(f"✅ Open API 조회 성공\n- **화합물명**: {api_res['title']}\n- **분자량**: {api_res['molecular_weight']} g/mol")
            
            # DB 매칭 검사
            key_match = user_query.strip().lower()
            if key_match in REAL_DRUG_PK_DATABASE:
                pk_info = REAL_DRUG_PK_DATABASE[key_match]
                selected_half_life = pk_info["half_life"]
                selected_dose = pk_info["standard_dose"]
                drug_display_name = pk_info["kr_name"]
                st.sidebar.info(f"매핑된 반감기({selected_half_life}시간)를 불어왔습니다.")
            else:
                st.sidebar.warning("API 검색은 성공했으나 반감기 매칭 데이터가 없어 기본값을 적용합니다. 직접 수치를 설정하세요.")
        else:
            st.sidebar.error(api_res["message"])

st.sidebar.header("⚙️ 2. 시뮬레이션 조건 설정")
initial_dose = st.sidebar.number_input("1회 복용량 (mg)", min_value=1.0, value=float(selected_dose), step=10.0)
half_life_val = st.sidebar.number_input("반감기 (시간)", min_value=0.1, value=float(selected_half_life), step=0.1)
obs_duration = st.sidebar.number_input("총 관찰 시간 (시간)", min_value=1.0, value=48.0, step=6.0)

simulation_type = st.sidebar.radio("투여 모델 선택", ["1회 단회 투여 (Single Dose)", "정기 반복 투여 (Multiple Doses)"])

dosing_interval = 6.0
if simulation_type == "정기 반복 투여 (Multiple Doses)":
    dosing_interval = st.sidebar.number_input("복용 간격 (시간)", min_value=1.0, value=float(half_life_val * 2), step=1.0)


# 메인 화면 시각화
st.subheader(f"📊 {drug_display_name} 잔존량 시뮬레이션 결과")

if simulation_type == "1회 단회 투여 (Single Dose)":
    times = np.linspace(0, obs_duration, 201)
    amounts = calculate_single_dose(initial_dose, half_life_val, times)
    percentages = (amounts / initial_dose) * 100
    
    df_res = pd.DataFrame({
        "경과 시간 (시간)": times,
        "잔존량 (mg)": amounts,
        "잔존 비율 (%)": percentages
    })
    
    # 지표 출력
    col1, col2, col3 = st.columns(3)
    col1.metric("종료 시점 잔존량", f"{amounts[-1]:.3f} mg")
    col2.metric("종료 시점 잔존 비율", f"{percentages[-1]:.3f} %")
    col3.metric("권장 참조 복용 간격 (1~2 T1/2)", f"{half_life_val:.1f} ~ {half_life_val*2:.1f} 시간")
    
    # Line Chart
    st.line_chart(df_res.set_index("경과 시간 (시간)")[["잔존량 (mg)"]])

else:
    times, amounts = calculate_multiple_doses(initial_dose, half_life_val, dosing_interval, obs_duration)
    df_res = pd.DataFrame({
        "경과 시간 (시간)": times,
        "체내 누적 잔존량 (mg)": amounts
    })
    
    peak_val = np.max(amounts)
    trough_val = amounts[-1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("최고 체내 잔존량 (Peak)", f"{peak_val:.2f} mg")
    col2.metric("관찰 종료 시점 잔존량", f"{trough_val:.2f} mg")
    col3.metric("설정된 복용 간격", f"{dosing_interval:.1f} 시간")
    
    st.line_chart(df_res.set_index("경과 시간 (시간)")[["체내 누적 잔존량 (mg)"]])

# 계산 원리 및 세부 정보
with st.expander("🔬 약동학 수학 모델 및 API 연동 구조 설명"):
    st.latex(r"A(t) = A_0 \cdot \left(\frac{1}{2}\right)^{\frac{t}{T_{1/2}}}")
    st.markdown("""
    - **Open API 연동**: PubChem REST API를 호출하여 화학 물질 고유 ID(CID) 및 표준 메타데이터를 수신합니다.
    - **1구획 일차 제거 모델**: 체내 약물이 일정 비율로 대사/배설된다고 가정하는 기본 연속 수치 모델입니다.
    - **반복 투여 누적 모델**: 일정 간격 $\\tau$ 마다 약물이 추가될 때 체내 중첩 반응을 계산하여 정상 상태(Steady-State) 도달 양상을 추론합니다.
    """)
