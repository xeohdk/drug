import numpy as np
import pandas as pd
import streamlit as st


def calculate_remaining(initial_amount, half_life, elapsed_time):
    """일차 제거 모델에 따른 잔존량(mg)을 계산한다."""
    return initial_amount * np.power(0.5, elapsed_time / half_life)


# 페이지 기본 설정
st.set_page_config(
    page_title="가상 약물 잔존량 학습",
    layout="centered"
)

# 제목 및 주의사항 안내
st.title("가상 약물 잔존량 학습 시뮬레이터")
st.warning(
    "가상의 조건을 이용하는 교육용 프로그램입니다. "
    "실제 복용량, 복용 간격, 약효 또는 안전성을 판단할 수 없습니다."
)
st.write(
    "초기량과 반감기를 바꾸며 시간에 따른 잔존량을 확인하세요. "
    "초기 시점에 약물이 이미 체내에 있고, 일정한 반감기로 제거된다고 가정합니다."
)

# 입력 폼 구성
with st.form("simulation_form"):
    initial_amount = st.number_input(
        "초기량 (mg)",
        min_value=0.0,
        max_value=10000.0,
        value=100.0,
        step=10.0,
        format="%.2f"
    )
    half_life = st.number_input(
        "반감기 (시간)",
        min_value=0.0,
        max_value=1000.0,
        value=4.0,
        step=0.5,
        format="%.2f"
    )
    duration = st.number_input(
        "관찰 시간 (시간)",
        min_value=0.0,
        max_value=1000.0,
        value=24.0,
        step=1.0,
        format="%.2f"
    )
    submitted = st.form_submit_button("계산하기")

# 계산 및 결과 시각화
if submitted:
    values = [initial_amount, half_life, duration]
    
    # 예외 처리 및 유효성 검사
    if not all(np.isfinite(value) for value in values):
        st.error("유한한 숫자를 입력해 주세요.")
        st.stop()

    if initial_amount <= 0:
        st.error("초기량은 0mg보다 크게 입력해 주세요.")
        st.stop()

    if half_life <= 0:
        st.error("반감기는 0시간보다 크게 입력해 주세요.")
        st.stop()

    if duration <= 0:
        st.error("관찰 시간은 0시간보다 크게 입력해 주세요.")
        st.stop()

    # 데이터 연산 (관찰 구간을 201개 지점으로 분할)
    times = np.linspace(0.0, duration, 201)
    amounts = calculate_remaining(initial_amount, half_life, times)
    percentages = (amounts / initial_amount) * 100

    result = pd.DataFrame({
        "경과 시간 (시간)": times,
        "추정 잔존량 (mg)": amounts,
        "초기량 대비 비율 (%)": percentages
    })

    final_amount = float(amounts[-1])
    final_percentage = float(percentages[-1])

    # 주요 계산 결과 지표
    st.subheader("계산 결과")
    st.caption(
        f"초기량 {initial_amount:g}mg / "
        f"반감기 {half_life:g}시간 / "
        f"관찰 시간 {duration:g}시간"
    )
    col1, col2 = st.columns(2)
    col1.metric("관찰 종료 시점 잔존량", f"{final_amount:.6g} mg")
    col2.metric("초기량 대비 잔존 비율", f"{final_percentage:.6g}%")

    # 잔존량 변화 추이 그래프
    st.subheader("시간에 따른 잔존량")
    graph_data = result.set_index("경과 시간 (시간)")
    st.line_chart(graph_data[["추정 잔존량 (mg)"]])

    # 시간별 세부 계산표
    st.subheader("시간별 계산표")
    st.dataframe(
        result.style.format({
            "경과 시간 (시간)": "{:.3f}",
            "추정 잔존량 (mg)": "{:.6g}",
            "초기량 대비 비율 (%)": "{:.6g}"
        }),
        use_container_width=True
    )

    st.info(
        "매 반감기마다 그때 남아 있는 양의 절반이 제거됩니다. "
        "이 모델에서 잔존량 감소가 곧 약효 감소를 뜻하지는 않습니다."
    )
    st.caption(
        "매우 작은 값은 표시 정밀도나 컴퓨터의 수치 표현 한계에 "
        "영향을 받을 수 있습니다. 화면에 0이 표시되더라도 "
        "실제 약물이 완전히 제거되었다는 뜻은 아닙니다."
    )

    # 모델 한계 설명
    with st.expander("계산 원리와 모델의 한계"):
        st.latex(r"A(t)=A_0 \times (1/2)^{t/T}")
        st.write(
            "A₀는 초기량, t는 경과 시간, T는 반감기입니다. "
            "흡수 과정, 조직 분포, 개인별 대사 차이, "
            "반복 투여와 비선형 제거는 반영하지 않습니다."
        )
        st.write(
            "입력 상한은 프로그램 운영을 위한 범위이며 "
            "의학적으로 안전한 양이나 시간을 의미하지 않습니다."
        )
