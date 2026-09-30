import streamlit as st
from pathlib import Path
import geopandas as gpd
import pandas as pd

st.set_page_config(
    page_title="15分钟宜居生活圈智能分析平台",
    page_icon="🏙️",
    layout="wide"
)

css_file = Path("assets/style.css")
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

DATA_PROCESSED = Path("data/processed")
STUDY_AREA_FILE = DATA_PROCESSED / "study_area.shp"

from modules.path_config import (
    init_paths, get_output_dir, set_output_dir,
    get_fig_dir, get_tab_dir
)

init_paths()

with st.spinner("正在检查数据..."):
    from modules.data_downloader import ensure_data
    ensure_data()

if "app_initialized" not in st.session_state:
    st.session_state["app_initialized"] = True

    for pattern in ["study_area.*", "road_clean.*", "poi_clean.*",
                    "isochrone.*", "communities.*", "building_clean.*"]:
        for f in DATA_PROCESSED.glob(pattern):
            try:
                f.unlink()
            except Exception:
                pass

    try:
        for d in [get_fig_dir(), get_tab_dir()]:
            for f in Path(d).glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass

        geotiff_dir = get_output_dir() / "geotiff"
        if geotiff_dir.exists():
            for f in geotiff_dir.glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception:
        pass


def card(content):
    return f'<div style="background:white;border-radius:16px;padding:22px 26px;box-shadow:0 2px 14px rgba(13,44,84,0.06);border:1px solid rgba(13,44,84,0.04);line-height:2;color:#2c3e50;">{content}</div>'


def hero(title, subtitle, desc):
    return f'<div style="background:linear-gradient(135deg,#0a2540 0%,#1a73e8 100%);border-radius:20px;padding:40px 44px;margin-bottom:32px;box-shadow:0 12px 36px rgba(13,44,84,0.22);position:relative;overflow:hidden;"><div style="position:absolute;top:-60px;right:-60px;width:220px;height:220px;background:radial-gradient(circle,rgba(255,255,255,0.12),transparent 70%);border-radius:50%;"></div><div style="position:relative;z-index:1;"><div style="color:white;margin:0;font-size:34px;font-weight:800;letter-spacing:-0.02em;">{title}</div><div style="color:#d6e4ff;margin:10px 0 0 0;font-weight:500;font-size:22px;">{subtitle}</div><div style="color:#a8c2e8;margin:14px 0 0 0;font-size:14.5px;">{desc}</div></div></div>'


def get_study_area_info():
    if not STUDY_AREA_FILE.exists():
        return None
    try:
        area = gpd.read_file(STUDY_AREA_FILE)
        cities = sorted(area["市"].dropna().unique().tolist()) if "市" in area.columns else []
        counties = sorted(area["县"].dropna().unique().tolist()) if "县" in area.columns else []
        return {
            "cities": cities,
            "counties": counties,
            "count": len(area),
        }
    except Exception:
        return None


def format_area_info(info):
    if not info:
        return None
    cities_str = "、".join(info["cities"]) if info["cities"] else "未知"
    counties_str = "、".join(info["counties"]) if info["counties"] else ""
    if counties_str:
        return f"{cities_str} → {counties_str}（共 {info['count']} 个地块）"
    return f"{cities_str}（共 {info['count']} 个地块）"


def clear_study_area():
    if STUDY_AREA_FILE.exists():
        STUDY_AREA_FILE.unlink()

    for pattern in ["study_area.*", "road_clean.*", "poi_clean.*",
                    "communities.*", "isochrone.*", "building_clean.*"]:
        for f in DATA_PROCESSED.glob(pattern):
            try:
                f.unlink()
            except Exception:
                pass

    try:
        for d in [get_fig_dir(), get_tab_dir()]:
            for f in Path(d).glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass

        geotiff_dir = get_output_dir() / "geotiff"
        if geotiff_dir.exists():
            for f in geotiff_dir.glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception:
        pass

    st.session_state["run_success"] = False
    st.session_state["run_error"] = None


with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:28px 0 16px 0;">
        <div style="width: 64px; height: 64px; margin: 0 auto 12px auto; background: linear-gradient(135deg, #1a73e8, #0d47a1); border-radius: 18px; display: flex; align-items: center; justify-content: center; font-size: 32px; box-shadow: 0 6px 18px rgba(26, 115, 232, 0.4);">🏙️</div>
        <div style="font-size:17px; font-weight:800; color:white;">15 分钟生活圈</div>
        <div style="font-size:13px; color:#8aa9d6; margin-top:4px;">Intelligent Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "navigation",
        ["🏠 首页总览", "🌏 研究区选择", "📥 数据准备与清洗",
         "🗺️ 生活圈划定", "📊 评价模型计算",
         "📈 一键出图", "📊 分析结果",
         "📁 输出路径设置", "⚙️ 优化建议与导出"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div style="text-align: center; color: #6b8bb8; font-size: 11px; padding-top: 30px;">
        V1.0 · Python + Streamlit
    </div>
    """, unsafe_allow_html=True)


if menu == "🏠 首页总览":
    st.markdown(hero(
        "🏙️ 15 分钟宜居生活圈",
        "智能分析平台",
        "支持广东省任意市 / 区县"
    ), unsafe_allow_html=True)

    if st.session_state.get("run_success"):
        st.success(f"✅ 运行成功：{st.session_state.get('run_message', '全流程运行完成')}")
        if st.button("关闭提示", key="close_run_msg"):
            st.session_state["run_success"] = False
            st.rerun()

    if st.session_state.get("run_error"):
        st.error(f"❌ 运行失败：{st.session_state['run_error']}")
        if st.button("关闭错误提示", key="close_err_msg"):
            st.session_state["run_error"] = None
            st.rerun()

    area_info = get_study_area_info()
    area_name = format_area_info(area_info)

    col_a, col_b = st.columns(2)
    with col_a:
        if area_name:
            st.success(f"📍 当前研究区：{area_name}")
        else:
            st.warning("📍 尚未设置研究区，请到「🌏 研究区选择」")
    with col_b:
        st.info(f"📁 当前输出路径：{get_output_dir()}")

    st.markdown("### 📊 数据总览")

    comm_file = DATA_PROCESSED / "communities.gpkg"
    poi_file = DATA_PROCESSED / "poi_clean.gpkg"
    road_file = DATA_PROCESSED / "road_clean.gpkg"
    iso_file = DATA_PROCESSED / "isochrone.gpkg"
    building_file = DATA_PROCESSED / "building_clean.gpkg"

    comm_count = "待提取"
    poi_count = "待提取"
    road_count = "待裁剪"
    iso_count = "待生成"
    building_count = "待裁剪"

    try:
        if comm_file.exists():
            comm_count = f"{len(gpd.read_file(comm_file, layer='communities'))}"
        if poi_file.exists():
            poi_count = f"{len(gpd.read_file(poi_file, layer='poi'))}"
        if road_file.exists():
            road_count = f"{len(gpd.read_file(road_file, layer='road'))}"
        if iso_file.exists():
            iso_count = "已生成"
        if building_file.exists():
            building_count = f"{len(gpd.read_file(building_file, layer='building'))}"
    except Exception as e:
        st.warning(f"读取数据时出错：{e}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("小区数量", str(comm_count))
    c2.metric("POI 数量", str(poi_count))
    c3.metric("路网数量", str(road_count))
    c4.metric("建筑数量", str(building_count))
    c5.metric("等时圈", str(iso_count))

    st.markdown("---")
    st.markdown("### 🚀 一键运行")

    if st.button("一键运行全流程", use_container_width=True):
        if not STUDY_AREA_FILE.exists():
            st.warning("请先到「🌏 研究区选择」设置研究区")
        else:
            st.session_state["run_success"] = False
            st.session_state["run_error"] = None

            progress = st.progress(0)
            status = st.empty()

            try:
                from modules.cleaner import run_clean
                from modules.isochrone import run_isochrone
                from modules.evaluation import run_evaluation
                from modules.visualization import run_all_figures
                from modules.analysis import generate_analysis_tables
                from modules.export_geotiff import export_all_geotiff

                for d in [get_fig_dir(), get_tab_dir()]:
                    for f in Path(d).glob("*"):
                        try:
                            f.unlink()
                        except Exception:
                            pass

                status.info("步骤 1/6：数据准备与清洗...")
                progress.progress(10)
                report = run_clean()
                for line in report:
                    st.write(line)
                progress.progress(25)

                status.info("步骤 2/6：生成 15 分钟生活圈...")
                run_isochrone()
                progress.progress(45)

                status.info("步骤 3/6：2SFCA + 熵权法评价...")
                run_evaluation()
                progress.progress(60)

                status.info("步骤 4/6：一键出图...")
                run_all_figures()
                progress.progress(75)

                status.info("步骤 5/6：生成分析表格...")
                generate_analysis_tables()
                progress.progress(90)

                status.info("步骤 6/6：导出 TIFF 和研究区边界...")
                export_all_geotiff()
                progress.progress(100)

                status.success("✅ 全流程运行完成")

                st.session_state["run_success"] = True
                st.session_state["run_message"] = "全流程运行完成"

                st.balloons()
                st.rerun()
            except Exception as e:
                status.error(f"运行出错：{e}")
                st.session_state["run_error"] = str(e)


elif menu == "🌏 研究区选择":
    st.markdown("## 🌏 研究区选择")

    st.markdown(card("<b>操作说明</b><br>① 选择城市（可多选）<br>② 选择区县（可留空 = 整个市）<br>③ 点击「确定研究区」<br>④ 若要换研究区，先点「清空研究区」再重新选择"), unsafe_allow_html=True)

    area_info = get_study_area_info()
    if area_info:
        cities_str = "、".join(area_info["cities"]) if area_info["cities"] else "未知"
        counties_str = "、".join(area_info["counties"]) if area_info["counties"] else ""
        if counties_str:
            st.info(f"📍 当前研究区：{cities_str} → {counties_str}（共 {area_info['count']} 个地块）")
        else:
            st.info(f"📍 当前研究区：{cities_str}（共 {area_info['count']} 个地块）")
    else:
        st.warning("📍 当前尚未设置研究区")

    st.markdown("---")

    from modules.region_selector import (
        list_cities, list_counties, set_study_area, get_study_area
    )

    try:
        cities = list_cities()
        selected_cities = st.multiselect(
            "① 选择城市（可多选）",
            options=cities,
            default=[]
        )

        counties = []
        if selected_cities:
            for c in selected_cities:
                counties.extend(list_counties(c))
            counties = sorted(set(counties))

        selected_counties = st.multiselect(
            "② 选择区县（可留空 = 整个市）",
            options=counties,
            default=[]
        )

        if selected_cities:
            st.caption(f"已选城市：{'、'.join(selected_cities)}")
        if selected_counties:
            st.caption(f"已选区县：{'、'.join(selected_counties)}")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ 确定研究区", use_container_width=True):
                if not selected_cities:
                    st.warning("请至少选择一个城市")
                else:
                    area = set_study_area(selected_cities, selected_counties)
                    st.success(f"✅ 已设置研究区，共 {len(area)} 个地块")
                    st.rerun()
        with col2:
            if st.button("🔄 查看当前研究区", use_container_width=True):
                try:
                    area = get_study_area()
                    cities_in = sorted(area["市"].dropna().unique().tolist()) if "市" in area.columns else []
                    counties_in = sorted(area["县"].dropna().unique().tolist()) if "县" in area.columns else []

                    if cities_in:
                        st.write(f"**已选城市**（{len(cities_in)} 个）：{'、'.join(cities_in)}")
                    if counties_in:
                        st.write(f"**已选区县**（{len(counties_in)} 个）：{'、'.join(counties_in)}")
                    st.write(f"**共包含 {len(area)} 个地块**")
                except Exception as e:
                    st.warning(f"尚未设置：{e}")
        with col3:
            if st.button("🗑️ 清空研究区", use_container_width=True):
                clear_study_area()
                st.success("✅ 已清空研究区，请重新选择")
                st.rerun()

    except FileNotFoundError:
        st.error("未找到行政区划数据")
    except Exception as e:
        st.error(f"出错：{e}")


elif menu == "📥 数据准备与清洗":
    st.markdown("## 📥 数据准备与清洗")
    st.markdown("---")

    if not STUDY_AREA_FILE.exists():
        st.warning("请先到「🌏 研究区选择」设置研究区")
    else:
        st.markdown("### 🛣️ 数据源")
        st.markdown(card("系统内置全国路网、全国 POI、广东省建筑轮廓、广东省人口、广东省夜间灯光。<br>点击下方按钮，自动按研究区裁剪所有数据。"), unsafe_allow_html=True)

        if st.button("🧹 一键准备全部数据", use_container_width=True):
            from modules.cleaner import run_clean
            with st.spinner("正在处理（可能需要几分钟）..."):
                try:
                    report = run_clean()
                    for line in report:
                        st.write(line)
                except Exception as e:
                    st.error(f"出错：{e}")


elif menu == "🗺️ 生活圈划定":
    st.markdown("## 🗺️ 15 分钟生活圈划定")

    st.markdown(card("<b>核心公式</b><br>基于真实路网的步行等时圈模型"), unsafe_allow_html=True)

    st.latex(r"T_{ij} = \sum_{k=1}^{n} \frac{L_{ijk}}{V_{walk}}")

    st.markdown("### ⚙️ 参数设置")
    col1, col2 = st.columns(2)
    with col1:
        speed = st.number_input("步行速度 (m/min)", value=80, min_value=40, max_value=120)
    with col2:
        minutes = st.number_input("时间阈值 (分钟)", value=15, min_value=5, max_value=30)

    st.markdown("---")
    if st.button("🗺️ 生成等时圈", use_container_width=True):
        comm_file = DATA_PROCESSED / "communities.gpkg"
        road_file = DATA_PROCESSED / "road_clean.gpkg"
        if not comm_file.exists():
            st.warning("小区数据未生成，请先去「📥 数据准备与清洗」")
        elif not road_file.exists():
            st.warning("路网数据未裁剪，请先去「📥 数据准备与清洗」")
        else:
            from modules.isochrone import run_isochrone
            with st.spinner("生成中..."):
                try:
                    iso = run_isochrone(speed, minutes)
                    st.success(f"✅ 已生成 {len(iso)} 个等时圈")
                    display_cols = [c for c in iso.columns if c != "geometry"]
                    st.dataframe(iso[display_cols].head(20), use_container_width=True)
                except Exception as e:
                    st.error(f"生成出错：{e}")


elif menu == "📊 评价模型计算":
    st.markdown("## 📊 评价模型计算")
    st.markdown("---")

    st.markdown("### 🧮 嵌入的核心公式")

    st.markdown("#### 一、基于真实路网的 15 分钟生活圈划定")

    st.markdown("**1. 步行时间**")
    st.latex(r"T_{ij} = \sum_{k=1}^{n} \frac{L_{ijk}}{V_{walk}}")

    st.markdown("**2. 设施覆盖率**")
    st.latex(r"C_{ij} = \begin{cases} 1, & \exists F_j \subset N(C_{is}) \\ 0, & \text{others} \end{cases}")

    st.markdown("**3. 设施达标率**")
    st.latex(r"CR_{ij} = \frac{\sum_{s=1}^{m_i} C_{ij,s}}{m_i}")

    st.markdown("#### 二、两步移动搜索法（2SFCA）")

    st.markdown("**4. 供需比**")
    st.latex(r"R_j = \frac{S_j}{\sum_{k \in \{d_{kj} \leq d_0\}} P_k \cdot G(d_{kj})}")

    st.markdown("**5. 可达性**")
    st.latex(r"A_i = \sum_{j \in \{d_{ij} \leq d_0\}} R_j \cdot G(d_{ij})")

    st.markdown("#### 三、熵权法综合便利度")

    st.markdown("**6. 数据标准化**")
    st.latex(r"x'(i,j) = \frac{x(i,j) - \min(x_j)}{\max(x_j) - \min(x_j)}")

    st.markdown("**7. 熵值计算**")
    st.latex(r"E_j = -k \sum_{i=1}^{n} P_{ij} \ln P_{ij}, \quad P_{ij} = \frac{x'(i,j)}{\sum_{i=1}^{n} x'(i,j)}")

    st.markdown("**8. 权重计算**")
    st.latex(r"w_j = \frac{1 - E_j}{M - \sum_{j=1}^{M} E_j}")

    st.markdown("**9. 综合便利度**")
    st.latex(r"Z_i = \sum_{j=1}^{M} w_j \cdot x'(i,j)")

    st.markdown("#### 四、位置分配模型优化")

    st.markdown("**10. 最小化阻抗模型**")
    st.latex(r"\min \sum_{i \in I} \sum_{j \in J} d_{ij} \cdot x_{ij}")

    st.markdown("**11. 最小化设施点模型**")
    st.latex(r"\min \sum_{j \in J} y_j")

    st.markdown("**12. 约束条件**")
    st.latex(r"\sum_{j \in J} x_{ij} = 1, \quad x_{ij} \leq y_j, \quad \forall i \in I, j \in J")

    st.markdown("---")

    if st.button("📊 开始评价", use_container_width=True):
        comm_file = DATA_PROCESSED / "communities.gpkg"
        poi_file = DATA_PROCESSED / "poi_clean.gpkg"
        iso_file = DATA_PROCESSED / "isochrone.gpkg"

        if not comm_file.exists() or not poi_file.exists():
            st.warning("小区或 POI 数据未准备，请先去「📥 数据准备与清洗」")
        elif not iso_file.exists():
            st.warning("请先生成等时圈")
        else:
            from modules.evaluation import run_evaluation
            with st.spinner("计算中..."):
                try:
                    df = run_evaluation()
                    st.success(f"✅ 计算完成，结果已保存到 {get_tab_dir()}")
                    st.dataframe(df.head(20), use_container_width=True)
                except Exception as e:
                    st.error(f"计算出错：{e}")


elif menu == "📈 一键出图":
    st.markdown("## 📈 一键出图")
    st.markdown("---")

    if st.button("🎨 生成全部图件", use_container_width=True):
        comm_file = DATA_PROCESSED / "communities.gpkg"
        poi_file = DATA_PROCESSED / "poi_clean.gpkg"
        iso_file = DATA_PROCESSED / "isochrone.gpkg"

        if not comm_file.exists() or not poi_file.exists() or not iso_file.exists():
            st.warning("请先完成数据准备、等时圈、评价等步骤")
        else:
            from modules.visualization import run_all_figures
            with st.spinner("出图中..."):
                try:
                    run_all_figures()
                    st.success(f"✅ 图件已生成到 {get_fig_dir()}")
                except Exception as e:
                    st.error(f"出图出错：{e}")

    st.markdown("---")

    if st.button("📦 导出 TIFF 与研究区边界", use_container_width=True):
        from modules.export_geotiff import export_all_geotiff
        with st.spinner("导出中..."):
            try:
                out_dir = export_all_geotiff()
                st.success(f"✅ TIFF 和研究区边界已导出到 {out_dir}")
            except Exception as e:
                st.error(f"导出出错：{e}")

    figs = sorted(get_fig_dir().glob("*.png"))
    if figs:
        st.markdown(f"### 🖼️ 已生成 {len(figs)} 张成果图")
        for f in figs:
            st.markdown(f"#### {f.stem}")
            st.image(str(f), use_container_width=True)
    else:
        st.info("暂无图件")


elif menu == "📊 分析结果":
    st.markdown("## 📊 分析结果")
    st.markdown("---")

    tab_dir = get_tab_dir()
    st.caption(f"当前读取目录：{tab_dir}")

    excel_files = sorted(tab_dir.glob("*.xlsx"))

    if not excel_files:
        st.warning("暂无分析结果，请先运行「一键运行全流程」或「开始评价」")
    else:
        st.markdown(f"### 📋 已生成 {len(excel_files)} 张分析表")

        for f in excel_files:
            st.markdown(f"#### 📄 {f.stem}")
            try:
                df = pd.read_excel(f)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"读取失败：{e}")
            st.markdown("---")


elif menu == "📁 输出路径设置":
    st.markdown("## 📁 输出路径设置")

    st.markdown(card("设置成果图、结果表的存储位置。<br>默认保存在项目下的 outputs 文件夹，也可以改成任意磁盘路径。"), unsafe_allow_html=True)

    st.markdown("---")

    current = str(get_output_dir())
    st.info(f"📁 当前输出路径：{current}")

    new_path = st.text_input("输入新的输出路径", value=current)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 应用新路径", use_container_width=True):
            try:
                p = set_output_dir(new_path)
                st.success(f"已切换到：{p}")
                st.rerun()
            except Exception as e:
                st.error(f"设置失败：{e}")

    with col2:
        if st.button("🔄 恢复默认路径", use_container_width=True):
            from config import OUTPUT_ROOT
            set_output_dir(str(OUTPUT_ROOT))
            st.success("已恢复默认路径")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📂 目录结构")
    st.write(f"- 图片（PNG）：`{get_fig_dir()}`")
    st.write(f"- 表格（Excel）：`{get_tab_dir()}`")
    st.write(f"- 栅格（TIFF）：`{get_output_dir() / 'geotiff'}`")
    st.write(f"- 研究区边界（SHP）：`{get_output_dir() / 'geotiff' / 'study_area.shp'}`")


elif menu == "⚙️ 优化建议与导出":
    st.markdown("## ⚙️ 优化建议与导出")
    st.markdown("---")

    st.markdown("### 🧮 位置分配模型公式")

    st.markdown("**最小化阻抗模型**")
    st.latex(r"\min \sum_{i \in I} \sum_{j \in J} d_{ij} \cdot x_{ij}")

    st.markdown("**最小化设施点模型**")
    st.latex(r"\min \sum_{j \in J} y_j")

    st.markdown("**约束条件**")
    st.latex(r"\sum_{j \in J} x_{ij} = 1, \quad x_{ij} \leq y_j, \quad \forall i \in I, j \in J")

    st.markdown("---")

    if st.button("⚙️ 运行位置分配优化", use_container_width=True):
        comm_file = DATA_PROCESSED / "communities.gpkg"
        poi_file = DATA_PROCESSED / "poi_clean.gpkg"
        iso_file = DATA_PROCESSED / "isochrone.gpkg"

        if not comm_file.exists() or not poi_file.exists() or not iso_file.exists():
            st.warning("请先完成数据准备、等时圈、评价等步骤")
        else:
            from modules.optimizer import run_optimization
            with st.spinner("优化中..."):
                try:
                    df = run_optimization()
                    st.success(f"✅ 优化完成，结果已保存到 {get_tab_dir()}")
                    st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"优化出错：{e}")

    st.markdown("---")
    st.markdown("### 📁 导出文件位置")
    st.write(f"- 图片（PNG）：`{get_fig_dir()}`")
    st.write(f"- 表格（Excel）：`{get_tab_dir()}`")
    st.write(f"- 栅格（TIFF）：`{get_output_dir() / 'geotiff'}`")
    st.write(f"- 研究区边界（SHP）：`{get_output_dir() / 'geotiff' / 'study_area.shp'}`")

    tbls = sorted(get_tab_dir().glob("*.xlsx"))
    if tbls:
        st.markdown("**已生成的结果表**")
        for t in tbls:
            st.write(f"- {t.name}")