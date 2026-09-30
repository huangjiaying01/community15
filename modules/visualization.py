import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import numpy as np
from matplotlib.patches import Patch, Polygon
from config import DATA_PROCESSED
from modules.path_config import get_fig_dir, get_tab_dir

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

STUDY_AREA = DATA_PROCESSED / "study_area.shp"


def _save(fig, name):
    fig.savefig(get_fig_dir() / name, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _get_study_area():
    if STUDY_AREA.exists():
        return gpd.read_file(STUDY_AREA)
    return None


def _add_north_arrow(ax):
    x = 0.88
    y = 0.85
    w = 0.022
    h_up = 0.040
    h_down = 0.013
    points = [
        (x, y + h_up),
        (x - w, y - h_up * 0.5),
        (x, y - h_up * 0.5 + h_down),
        (x + w, y - h_up * 0.5),
    ]
    arrow = Polygon(points, closed=True, transform=ax.transAxes,
                    facecolor="none", edgecolor="black",
                    linewidth=2.0, zorder=12, joinstyle="miter")
    ax.add_patch(arrow)
    ax.text(x + w * 1.4, y + h_up * 0.3, "N",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=14, fontweight="bold", color="black", zorder=13)


def _add_scale_bar(ax):
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    length = (xlim[1] - xlim[0]) * 0.15
    x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.78
    y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.03
    ax.plot([x_start, x_start + length], [y_pos, y_pos],
            color="black", linewidth=3)
    ax.text(x_start + length / 2, y_pos + (ylim[1] - ylim[0]) * 0.008,
            f"{length * 100:.0f} km", ha="center", va="bottom", fontsize=10)


def _plot_boundary(ax, study_area):
    if study_area is not None:
        study_area.boundary.plot(ax=ax, color="black", linewidth=2)


def run_all_figures():
    road = gpd.read_file(DATA_PROCESSED / "road_clean.gpkg", layer="road")
    poi = gpd.read_file(DATA_PROCESSED / "poi_clean.gpkg", layer="poi")
    iso = gpd.read_file(DATA_PROCESSED / "isochrone.gpkg", layer="isochrone")
    communities = gpd.read_file(DATA_PROCESSED / "communities.gpkg", layer="communities")
    study_area = _get_study_area()

    fig, ax = plt.subplots(figsize=(12, 11))
    road.plot(ax=ax, linewidth=0.4, color="#999999")
    communities.plot(ax=ax, markersize=12, color="#1a73e8",
                     edgecolor="white", linewidth=0.5)
    _plot_boundary(ax, study_area)
    legend_elements = [
        plt.Line2D([0], [0], color="#999999", linewidth=1.5, label="路网"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#1a73e8",
                   markersize=8, label="居住小区"),
        plt.Line2D([0], [0], color="black", linewidth=2, label="研究区边界"),
    ]
    ax.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, -0.06), fontsize=11, ncol=3, frameon=False)
    ax.set_title("研究区路网与居住小区分布图", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _add_scale_bar(ax)
    _save(fig, "01_研究区路网与居住小区分布图.png")

    fig, ax = plt.subplots(figsize=(12, 11))
    colors = {
        "education": "#e53935", "medical": "#1e88e5", "commercial": "#43a047",
        "transport": "#fb8c00", "elderly": "#8e24aa", "park": "#00acc1",
        "sports": "#fdd835", "culture": "#6d4c41",
    }
    for ftype, color in colors.items():
        sub = poi[poi["type"] == ftype]
        if len(sub) > 0:
            sub.plot(ax=ax, markersize=6, color=color, alpha=0.7)
    _plot_boundary(ax, study_area)
    legend_elements = [
        Patch(facecolor=c, label=t) for t, c in colors.items() if len(poi[poi["type"] == t]) > 0
    ]
    ax.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, -0.06), fontsize=10, ncol=4, frameon=False)
    ax.set_title("各类设施核密度分析图", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _add_scale_bar(ax)
    _save(fig, "02_各类设施核密度分析图.png")

    fig, ax = plt.subplots(figsize=(12, 11))
    iso.plot(ax=ax, alpha=0.4, edgecolor="#2e7d32", linewidth=0.6)
    communities.plot(ax=ax, markersize=10, color="#1a73e8")
    _plot_boundary(ax, study_area)
    legend_elements = [
        Patch(facecolor="#2e7d32", alpha=0.4, label="15分钟可达范围"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="#1a73e8",
                   markersize=8, label="居住小区"),
        plt.Line2D([0], [0], color="black", linewidth=2, label="研究区边界"),
    ]
    ax.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, -0.06), fontsize=11, ncol=3, frameon=False)
    ax.set_title("15 分钟生活圈范围图", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _add_scale_bar(ax)
    _save(fig, "03_15分钟生活圈范围图.png")

    cov = []
    for idx, row in iso.iterrows():
        cnt = len(poi[poi.within(row.geometry)])
        cov.append({"community_id": row.community_id, "count": cnt,
                    "geometry": row.geometry})
    cov_gdf = gpd.GeoDataFrame(cov, crs=iso.crs)

    fig, ax = plt.subplots(figsize=(13, 11))
    cov_gdf.plot(ax=ax, column="count", cmap="YlOrRd", legend=True,
                 edgecolor="white", linewidth=0.3,
                 legend_kwds={"label": "设施数量", "shrink": 0.6, "pad": 0.02})
    _plot_boundary(ax, study_area)
    ax.set_title("设施覆盖率与达标率空间分布图", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _save(fig, "04_设施覆盖率与达标率空间分布图.png")

    eval_file = get_tab_dir() / "evaluation.xlsx"
    if eval_file.exists():
        eval_df = pd.read_excel(eval_file)
        eval_gdf = iso.merge(eval_df, on="community_id", how="left")

        access_cols = [c for c in eval_gdf.columns if c.endswith("_access")]
        if access_cols:
            eval_gdf["total_access"] = eval_gdf[access_cols].sum(axis=1)
            fig, ax = plt.subplots(figsize=(13, 11))
            eval_gdf.plot(ax=ax, column="total_access", cmap="RdYlGn",
                          legend=True, edgecolor="white", linewidth=0.3,
                          legend_kwds={"label": "2SFCA可达性指数", "shrink": 0.6})
            _plot_boundary(ax, study_area)
            ax.set_title("2SFCA 供需匹配度空间分布图", fontsize=16, fontweight="bold", pad=15)
            ax.set_xlabel("经度 (°E)", fontsize=12)
            ax.set_ylabel("纬度 (°N)", fontsize=12)
            _add_north_arrow(ax)
            _save(fig, "05_2SFCA供需匹配度空间分布图.png")

        if "composite_index" in eval_gdf.columns:
            fig, ax = plt.subplots(figsize=(13, 11))
            eval_gdf.plot(ax=ax, column="composite_index", cmap="viridis",
                          legend=True, edgecolor="white", linewidth=0.3,
                          legend_kwds={"label": "综合便利度指数", "shrink": 0.6})
            _plot_boundary(ax, study_area)
            ax.set_title("综合便利度指数分级图", fontsize=16, fontweight="bold", pad=15)
            ax.set_xlabel("经度 (°E)", fontsize=12)
            ax.set_ylabel("纬度 (°N)", fontsize=12)
            _add_north_arrow(ax)
            _save(fig, "06_综合便利度指数分级图.png")

    blind = cov_gdf[cov_gdf["count"] == 0]
    fig, ax = plt.subplots(figsize=(12, 11))
    iso.plot(ax=ax, alpha=0.3, color="#cccccc")
    if len(blind) > 0:
        blind.plot(ax=ax, color="#d32f2f", edgecolor="white", linewidth=0.5)
    _plot_boundary(ax, study_area)
    legend_elements = [
        Patch(facecolor="#cccccc", alpha=0.3, label="已覆盖区域"),
        Patch(facecolor="#d32f2f", label=f"服务盲区（{len(blind)} 个）"),
        plt.Line2D([0], [0], color="black", linewidth=2, label="研究区边界"),
    ]
    ax.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, -0.06), fontsize=11, ncol=3, frameon=False)
    ax.set_title("设施服务盲区分布图", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _add_scale_bar(ax)
    _save(fig, "07_设施服务盲区分布图.png")

    fig, axes = plt.subplots(1, 2, figsize=(22, 11))
    cov_gdf.plot(ax=axes[0], column="count", cmap="YlOrRd", legend=True,
                 edgecolor="white", linewidth=0.3,
                 legend_kwds={"label": "设施数量", "shrink": 0.5})
    _plot_boundary(axes[0], study_area)
    axes[0].set_title("优化前设施覆盖率", fontsize=14, fontweight="bold")
    _add_north_arrow(axes[0])
    blind_after = blind.copy()
    if len(blind_after) > 0:
        blind_after["count"] = 1
    optimized = pd.concat([cov_gdf[cov_gdf["count"] > 0], blind_after])
    optimized.plot(ax=axes[1], column="count", cmap="YlOrRd", legend=True,
                   edgecolor="white", linewidth=0.3,
                   legend_kwds={"label": "设施数量", "shrink": 0.5})
    _plot_boundary(axes[1], study_area)
    axes[1].set_title("优化后设施覆盖率", fontsize=14, fontweight="bold")
    _add_north_arrow(axes[1])
    plt.suptitle("优化前后设施覆盖率对比图", fontsize=16, fontweight="bold", y=0.98)
    plt.tight_layout()
    _save(fig, "08_优化前后设施覆盖率对比图.png")

    fig, ax = plt.subplots(figsize=(12, 11))
    iso.plot(ax=ax, alpha=0.3, color="#cccccc")
    if len(blind) > 0:
        blind.plot(ax=ax, color="#d32f2f", edgecolor="white",
                   linewidth=0.5, markersize=80)
    _plot_boundary(ax, study_area)
    legend_elements = [
        Patch(facecolor="#cccccc", alpha=0.3, label="已覆盖区域"),
        Patch(facecolor="#d32f2f", label=f"建议增补设施（{len(blind)} 个）"),
    ]
    ax.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, -0.06), fontsize=11, ncol=2, frameon=False)
    ax.set_title("基于位置分配模型的设施增补建议图",
                 fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _add_scale_bar(ax)
    _save(fig, "09_设施增补建议图.png")

    _draw_statistical_charts(poi, cov_gdf, eval_file)

    return True


def _draw_statistical_charts(poi, cov_gdf, eval_file):
    colors_pie = ["#e53935", "#1e88e5", "#43a047", "#fb8c00",
                  "#8e24aa", "#00acc1", "#fdd835", "#6d4c41"]

    fig, ax = plt.subplots(figsize=(12, 8))
    type_counts = poi["type"].value_counts()
    bars = ax.bar(type_counts.index, type_counts.values,
                  color=colors_pie[:len(type_counts)])
    for bar, val in zip(bars, type_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100,
                str(val), ha="center", va="bottom", fontsize=10)
    ax.set_xlabel("设施类型", fontsize=12)
    ax.set_ylabel("设施数量（个）", fontsize=12)
    ax.set_title("各类设施数量统计柱状图", fontsize=15, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    _save(fig, "10_各类设施数量柱状图.png")

    fig, ax = plt.subplots(figsize=(10, 10))
    wedges, texts, autotexts = ax.pie(
        type_counts.values, labels=type_counts.index,
        autopct="%1.1f%%", colors=colors_pie[:len(type_counts)],
        startangle=90, textprops={"fontsize": 11}
    )
    for t in autotexts:
        t.set_fontsize(10)
        t.set_color("white")
        t.set_fontweight("bold")
    ax.set_title("各类设施占比饼图", fontsize=15, fontweight="bold", pad=15)
    plt.tight_layout()
    _save(fig, "11_各类设施占比饼图.png")

    fig, ax = plt.subplots(figsize=(12, 8))
    counts = cov_gdf["count"].values
    n, bins, patches = ax.hist(counts, bins=30, color="#1a73e8",
                                edgecolor="white", alpha=0.8)
    ax.set_xlabel("15分钟生活圈内设施数量", fontsize=12)
    ax.set_ylabel("小区数量（个）", fontsize=12)
    ax.set_title("设施覆盖数量分布直方图", fontsize=15, fontweight="bold", pad=15)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    _save(fig, "12_设施覆盖分布直方图.png")

    fig, ax = plt.subplots(figsize=(12, 8))
    if eval_file.exists():
        eval_df = pd.read_excel(eval_file)
        acc_cols = [c for c in eval_df.columns if c.endswith("_access")]
        if acc_cols:
            means = [eval_df[c].mean() for c in acc_cols]
            labels = [c.replace("_access", "") for c in acc_cols]
            bars = ax.barh(labels, means, color="#43a047")
            for bar, val in zip(bars, means):
                ax.text(bar.get_width() + 0.001,
                        bar.get_y() + bar.get_height() / 2,
                        f"{val:.4f}", va="center", fontsize=10)
            ax.set_xlabel("平均可达性指数", fontsize=12)
            ax.set_title("各类设施平均可达性对比（2SFCA）",
                         fontsize=15, fontweight="bold", pad=15)
            ax.grid(axis="x", alpha=0.3, linestyle="--")
    plt.tight_layout()
    _save(fig, "13_各类设施平均可达性对比图.png")

    fig, ax = plt.subplots(figsize=(11, 11))
    x = poi.geometry.x
    y = poi.geometry.y
    h = ax.hexbin(x, y, gridsize=40, cmap="YlOrRd", mincnt=1)
    plt.colorbar(h, ax=ax, label="设施密度", shrink=0.7)
    if STUDY_AREA.exists():
        study_area = gpd.read_file(STUDY_AREA)
        study_area.boundary.plot(ax=ax, color="black", linewidth=2)
    ax.set_title("设施点空间热力图", fontsize=15, fontweight="bold", pad=15)
    ax.set_xlabel("经度 (°E)", fontsize=12)
    ax.set_ylabel("纬度 (°N)", fontsize=12)
    _add_north_arrow(ax)
    _save(fig, "14_设施点空间热力图.png")