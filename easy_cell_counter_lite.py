import streamlit as st
import math
from datetime import datetime
import pandas as pd # (CSV 생성을 위해 pandas 필요)

# --- 1. 앱의 기본 설정 ---
st.set_page_config(page_title="세포 수 계산기 v36 (Lite)", layout="wide")
st.title("🔬 간단한 세포 수 계산기 v36 (Lite)")
st.write("실험 값을 입력하면, 필요한 배양액과 총 접시 수를 계산합니다.")

# --- 2. 입력 섹션 (Sidebar) ---
# (v35와 동일)
st.sidebar.header("[1단계] 세포 계수 정보")
num_squares_counted = st.sidebar.number_input(
    "1. 계수한 칸의 수", 
    min_value=1, max_value=9, value=4, step=1
)

live_cell_counts = [] 
dead_cell_counts = [] 
st.sidebar.write("각 칸의 세포 수를 입력하세요:")
for i in range(int(num_squares_counted)):
    col1, col2 = st.sidebar.columns(2)
    live_count = col1.number_input(f"   칸 {i+1} (Live)", min_value=0, value=50, step=1, key=f"calc_live_count_{i}")
    dead_count = col2.number_input(f"   칸 {i+1} (Dead)", min_value=0, value=0, step=1, key=f"calc_dead_count_{i}")
    live_cell_counts.append(live_count)
    dead_cell_counts.append(dead_count)

st.sidebar.divider() 
dilution = st.sidebar.number_input(
    "3. 카운팅 시 희석 배수", 
    min_value=1.0, value=2.0, step=0.1
)
total_stock_vol = st.sidebar.number_input(
    "4. 세포 현탁액 총 부피 (mL)", 
    min_value=0.0, value=5.0, step=0.1
)

st.sidebar.header("[2단계] 목표 조건 입력") 
default_target_cells = 5.0e5 
use_default = st.sidebar.radio(
    f"5. 목표 세포 수 (기본값: {default_target_cells:.2e}개)",
    ("기본값 사용", "직접 입력"), 
    index=0 
)
if use_default == "직접 입력":
    target_cells = st.sidebar.number_input(
        "   -> 원하는 총 세포 수를 입력하세요", 
        min_value=0.0, value=1000000.0, step=1000.0, format="%.0f"
    )
else:
    target_cells = default_target_cells

st.sidebar.header("[3단계] 분주용 현탁액 조건 입력") 
pipette_volume = st.sidebar.number_input(
    "6. 부피 (mL)", 
    min_value=0.1, value=2.0, step=0.1
)

# --- 3. 계산 함수 (v35와 동일) ---
def perform_calculation():
    try:
        if num_squares_counted <= 0: st.error("!오류: '계수한 칸의 수'는 0보다 커야 합니다."); return False
        
        total_live_cells_counted = sum(live_cell_counts)
        total_dead_cells_counted = sum(dead_cell_counts)
        total_all_cells_counted = total_live_cells_counted + total_dead_cells_counted
        avg_live_count = float(total_live_cells_counted) / float(num_squares_counted)
        if total_all_cells_counted > 0: viability = (float(total_live_cells_counted) / float(total_all_cells_counted)) * 100
        else: viability = 0.0 
        
        cells_per_ml = avg_live_count * dilution * 10000
        total_live_cells_in_tube = cells_per_ml * total_stock_vol
        if cells_per_ml == 0: st.error("!오류: 1단계에서 계산된 '살아있는' 세포 농도가 0입니다."); return False
        required_volume = target_cells / cells_per_ml
        available_dishes = int(total_live_cells_in_tube // target_cells)
        if pipette_volume <= 0: st.error("!오류: '심을 부피'는 0보다 커야 합니다."); return False
        concentration_working = target_cells / pipette_volume
        if cells_per_ml < concentration_working: st.error(f"⚠️ [제조 불가] 경고! 현탁액 농도({cells_per_ml:.2e})가 ..."); return False
        total_working_volume = total_live_cells_in_tube / concentration_working
        media_to_add = total_working_volume - total_stock_vol
        total_dishes_final = math.floor(total_working_volume / pipette_volume)
        
        st.session_state.results = {
            "cells_per_ml": cells_per_ml, "total_live_cells_in_tube": total_live_cells_in_tube,
            "total_stock_vol": total_stock_vol, "total_all_cells_counted": total_all_cells_counted,
            "total_live_cells_counted": total_live_cells_counted, "total_dead_cells_counted": total_dead_cells_counted,
            "viability": viability, "required_volume": required_volume, "available_dishes": available_dishes,
            "target_cells": target_cells, "pipette_volume": pipette_volume, "concentration_working": concentration_working,
            "total_working_volume": total_working_volume, "media_to_add": media_to_add,
            "total_dishes_final": total_dishes_final
        }
        return True # 계산 성공
    except Exception as e:
        st.error(f"계산 중 오류가 발생했습니다: {e}"); return False

# --- 4. 계산 실행 버튼 로직 (v35와 동일) ---
if st.sidebar.button("✨ 계산 실행하기 ✨", type="primary"):
    if perform_calculation():
        st.session_state.calculation_done = True
    else:
        st.session_state.calculation_done = False
        if "results" in st.session_state: del st.session_state.results

# --- 5. 결과 및 다운로드 (v36 수정됨) ---
if st.session_state.get("calculation_done", False) and "results" in st.session_state:
    
    results = st.session_state.results
    
    # (결과 출력 1, 2, 3 - v35와 동일)
    st.header("🔬 계산 결과")
    st.subheader("[1] 현재 세포 상태")
    col1, col2, col3 = st.columns(3)
    col1.metric("세포 현탁액 (Live) 농도", f"{results['cells_per_ml']:.2e} cells/mL")
    col2.metric("보유한 총 (Live) 세포 수", f"{results['total_live_cells_in_tube']:.2e} 개")
    col3.metric("보유한 현탁액 총 부피", f"{results['total_stock_vol']:.2f} mL")
    st.info(f"**세포 생존률 분석 (Counted)**\n\n- **총 세포 수:** {results['total_all_cells_counted']} 개\n- **살아있는 세포 수:** {results['total_live_cells_counted']} 개\n- **죽은 세포 수:** {results['total_dead_cells_counted']} 개\n- **세포 생존률 (Viability):** {results['viability']:.2f} %", icon="🔬")
    st.divider()
    st.subheader(f"[2] 현탁액 기준 ({results['target_cells']:.2e}개/접시)")
    col1, col2 = st.columns(2)
    col1.metric("'접시 1개' 필요 현탁액 부피", f"{results['required_volume']:.3f} mL")
    col2.metric("'총 준비 가능 배양접시 수'", f"{results['available_dishes']} 개")
    st.divider()
    st.subheader("[3] 분주용 현탁액 제조 (현탁액 모두 사용)")
    st.success("✅ **[분주용 현탁액 제조법]**")
    recipe_text = f"""
1. '세포 현탁액' {results['total_stock_vol']:.3f} mL (전체)에
2. '새 배지' {results['media_to_add']:.3f} mL를 더합니다.
------------------------------------------------
   총 {results['total_working_volume']:.3f} mL의 '분주용 현탁액'이 완성됩니다.
   (분주용 현탁액 농도: {results['concentration_working']:.2e} cells/mL)
    """
    st.code(recipe_text, language="text")
    st.success(f"➡️ **이 분주용 현탁액을 {results['pipette_volume']:.1f} mL씩 분주하면, 총 {results['total_dishes_final']}개의 배양접시를 만들 수 있습니다.**")

    # ▼▼▼ [신규] v36: 엑셀(CSV) 다운로드 (헤더 수정) ▼▼▼
    st.divider()
    st.subheader("⬇️ 계산 결과 다운로드")
    
    # 1. (입력 파라미터 수집 - 접두사 제거)
    inputs_base = {
        "계산 시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "계수한 칸 수": num_squares_counted,
        "희석 배수": dilution,
        "원액 총 부피 (mL)": total_stock_vol,
        "목표 세포 수": f"{target_cells:.2e}", # (요청 3: 지수 표기)
        "분주 부피 (mL)": pipette_volume,
    }
    
    # 2. (요청 1, 2: 칸별 데이터를 별도 열로 분리)
    count_inputs = {}
    for i in range(int(num_squares_counted)):
        count_inputs[f"Live Cell (칸 {i+1})"] = live_cell_counts[i]
        count_inputs[f"Dead Cell (칸 {i+1})"] = dead_cell_counts[i]

    # 3. (현재 세포 상태 수집 - 접두사 제거)
    status = {
        "Live 농도 (cells/mL)": f"{results['cells_per_ml']:.2e}",
        "총 Live 세포 수": f"{results['total_live_cells_in_tube']:.2e}",
        "Viability (%)": f"{results['viability']:.2f}",
        "Counted Live (합계)": results['total_live_cells_counted'],
        "Counted Dead (합계)": results['total_dead_cells_counted'],
    }
    
    # 4. (현탁액 기준 수집 - 접두사 제거)
    solution = {
        "추가할 새 배지 (mL)": f"{results['media_to_add']:.3f}",
        "최종 현탁액 부피 (mL)": f"{results['total_working_volume']:.3f}",
        "총 배양접시 수 (개)": results['total_dishes_final'],
        "분주용 현탁액 농도 (cells/mL)": f"{results['concentration_working']:.2e}"
    }

    # (모두 합치기)
    data_for_df = {**inputs_base, **count_inputs, **status, **solution}
    
    # (DataFrame 생성)
    df = pd.DataFrame([data_for_df])
    # (컬럼 순서는 딕셔너리 순서대로)

    @st.cache_data
    def to_csv(df_to_convert):
        return df_to_convert.to_csv(index=False).encode('utf-8-sig')

    csv_data = to_csv(df)
    
    st.download_button(
        label="📥 CSV (Excel) 파일로 저장하기",
        data=csv_data,
        file_name=f"cell_calculation_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime='text/csv',
    )
    # ▲▲▲ [신규] v36 ▲▲▲

else:
    # (앱의 초기 화면)
    st.info("왼쪽 사이드바에서 값을 입력하고 '계산 실행하기' 버튼을 눌러주세요.")
