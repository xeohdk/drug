import numpy as np
import pandas as pd
import streamlit as st


def calculate_remaining(initial_amount, half_life, elapsed_time):
    """일차 제거 모델에 따른 잔존량(mg)을 계산한다."""
    return initial_amount * np.power(0.5, elapsed_time / half_life)


def recommend_dosing_interval(half_life):
    """
    반감기를 바탕으로 학술적 기준의 권장 복용 간격 범위(시간)를 산출한다.
    (일반적으로 약동학 모델에서 정상 상태 유지를 위한 복용 간격은 반감기의 1~2배 수준임)
    """
    min_interval = half_life
    max_interval = half_life * 2.0
    return min_interval, max_interval


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

    # 데이터 연산
    times = np.linspace(0.0, duration, 201)
    amounts = calculate_remaining(initial_amount, half_life, times)
    percentages = (amounts / initial_amount) * 100

    # 학술적 복용 간격 추천 연산
    rec_min, rec_max = recommend_dosing_interval(half_life)

    result = pd.DataFrame({
        "경과 시간 (시간)": times,
        "추정 잔존량 (mg)": amounts,
        "초기량 대비 비율 (%)": percentages
    })

    final_amount = float(amounts[-1])
    final_percentage = float(percentages[-1])

    # 주요 계산 결과 및 권장 복용 간격 지표
    st.subheader("계산 결과")
    st.caption(
        f"초기량 {initial_amount:g}mg / "
        f"반감기 {half_life:g}시간 / "
        f"관찰 시간 {duration:g}시간"
    )
    
    col1, col2, col3 = st.columns(3)
    col1.metric("종료 시점 잔존량", f"{final_amount:.4g} mg")
    col2.metric("초기량 대비 비율", f"{final_percentage:.4g}%")
    col3.metric("참조 복용 간격", f"{rec_min:g} ~ {rec_max:g} 시간")

    st.info(
        f"💡 **학술적 참고 사항**: 입력된 반감기({half_life:g}시간)를 바탕으로 한 이론적 권장 복용 간격은 "
        f"**{rec_min:g}시간 ~ {rec_max:g}시간**입니다. (체내 잔존량이 $25\\% \\sim 50\\%$ 수준으로 떨어지는 시점)"
    )

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

    st.caption(
        "매우 작은 값은 표시 정밀도나 컴퓨터의 수치 표현 한계에 "
        "영향을 받을 수 있습니다. 화면에 0이 표시되더라도 "
        "실제 약물이 완전히 제거되었다는 뜻은 아닙니다."
    )

    # 모델 한계 및 원리 설명
    with st.expander("계산 원리와 모델의 한계"):
        st.latex(r"A(t)=A_0 \times (1/2)^{t/T}")
        st.write(
            "• **A₀**: 초기량, **t**: 경과 시간, **T**: 반감기\n"
            "• **복용 간격 추정 원리**: 약동학 기본 모델에서는 약물의 체내 적정 농도 유지를 위해 "
            "보통 반감기의 1배~2배 시점($T \\sim 2T$)을 참조 복용 간격으로 고찰합니다.\n"
            "• **한계점**: 본 계산은 단회 투여 기준 모델이며, 실제 임상에서는 치료 창(Therapeutic window), "
            "최소 유효 농도,독성 농도, 독성 역학, 개인별 대사율 등에 따라 복용 간격이 달라집니다."
        )
