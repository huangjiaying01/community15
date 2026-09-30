import geopandas as gpd
import pandas as pd
import numpy as np
from config import DATA_PROCESSED, FACILITY_TYPES, SEARCH_RADIUS
from modules.path_config import get_tab_dir


def generate_analysis_tables():
    communities = gpd.read_file(DATA_PROCESSED / "communities.gpkg", layer="communities").to_crs(4547)
    poi = gpd.read_file(DATA_PROCESSED / "poi_clean.gpkg", layer="poi").to_crs(4547)
    iso = gpd.read_file(DATA_PROCESSED / "isochrone.gpkg", layer="isochrone").to_crs(4547)

    tables = {}

    coverage_rows = []
    for idx, row in iso.iterrows():
        inside = poi[poi.within(row.geometry)]
        coverage_rows.append({
            "community_id": row.community_id,
            "total_poi": len(inside),
            "covered": 1 if len(inside) > 0 else 0
        })
    coverage_df = pd.DataFrame(coverage_rows)

    by_type = []
    for ftype in FACILITY_TYPES:
        fac = poi[poi["type"] == ftype]
        covered_count = 0
        for idx, row in iso.iterrows():
            if len(fac[fac.within(row.geometry)]) > 0:
                covered_count += 1
        coverage_rate = covered_count / len(iso) if len(iso) > 0 else 0
        by_type.append({
            "facility_type": ftype,
            "facility_count": len(fac),
            "covered_communities": covered_count,
            "coverage_rate": round(coverage_rate, 4)
        })
    coverage_by_type = pd.DataFrame(by_type)
    coverage_by_type.to_excel(get_tab_dir() / "01_设施覆盖率统计表.xlsx", index=False)
    tables["coverage_by_type"] = coverage_by_type

    total_rate = coverage_df["covered"].mean() if len(coverage_df) > 0 else 0
    summary = pd.DataFrame({
        "指标": [
            "研究区小区总数",
            "研究区 POI 总数",
            "被覆盖小区数",
            "未覆盖小区数",
            "整体覆盖率",
            "15分钟达标率",
        ],
        "值": [
            len(communities),
            len(poi),
            int(coverage_df["covered"].sum()),
            int(len(coverage_df) - coverage_df["covered"].sum()),
            round(total_rate, 4),
            round(total_rate, 4),
        ]
    })
    summary.to_excel(get_tab_dir() / "02_总体评价汇总表.xlsx", index=False)
    tables["summary"] = summary

    eval_file = get_tab_dir() / "evaluation.xlsx"
    if eval_file.exists():
        eval_df = pd.read_excel(eval_file)
        access_cols = [c for c in eval_df.columns if c.endswith("_access")]

        weight_rows = []
        for c in access_cols:
            ftype = c.replace("_access", "")
            weight_rows.append({
                "设施类型": ftype,
                "平均可达性": round(eval_df[c].mean(), 4),
                "最大值": round(eval_df[c].max(), 4),
                "最小值": round(eval_df[c].min(), 4),
                "标准差": round(eval_df[c].std(), 4),
            })
        weights_df = pd.DataFrame(weight_rows)
        weights_df.to_excel(get_tab_dir() / "03_各类设施可达性统计表.xlsx", index=False)
        tables["weights"] = weights_df

        if "composite_index" in eval_df.columns:
            eval_df["便利度等级"] = pd.cut(
                eval_df["composite_index"],
                bins=[-np.inf, 0.25, 0.5, 0.75, np.inf],
                labels=["低", "较低", "较高", "高"]
            )
            grade_counts = eval_df["便利度等级"].value_counts().reset_index()
            grade_counts.columns = ["便利度等级", "小区数量"]
            grade_counts.to_excel(get_tab_dir() / "04_综合便利度分级统计表.xlsx", index=False)
            tables["grade"] = grade_counts

            top10 = eval_df.nlargest(10, "composite_index")[
                ["community_id", "population", "composite_index"]
            ]
            top10.to_excel(get_tab_dir() / "05_便利度最高前10小区.xlsx", index=False)

            bottom10 = eval_df.nsmallest(10, "composite_index")[
                ["community_id", "population", "composite_index"]
            ]
            bottom10.to_excel(get_tab_dir() / "06_便利度最低前10小区.xlsx", index=False)

    blind = coverage_df[coverage_df["covered"] == 0]
    if len(blind) > 0:
        blind_stat = pd.DataFrame({
            "指标": ["服务盲区小区数", "盲区占比"],
            "值": [
                len(blind),
                round(len(blind) / len(coverage_df), 4) if len(coverage_df) > 0 else 0
            ]
        })
        blind_stat.to_excel(get_tab_dir() / "07_服务盲区统计表.xlsx", index=False)
        tables["blind"] = blind_stat

    return tables