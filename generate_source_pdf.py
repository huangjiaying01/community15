from fpdf import FPDF
from pathlib import Path

# ============ 配置 ============
PROJECT_ROOT = Path(__file__).parent
SOFTWARE_NAME = "15分钟宜居生活圈智能分析平台"
VERSION = "V1.0"
LINES_PER_PAGE = 50

CODE_EXTS = {".py", ".js", ".ts", ".css", ".html", ".json", ".sql", ".java", ".cpp", ".c", ".h"}
IGNORE_DIRS = {".venv", "venv", "__pycache__", ".git",
               "outputs", "data", "figures", "tables",
               "node_modules", ".idea", ".vscode", "assets"}

# 优先用项目里的 simhei.ttf，找不到就用系统黑体
LOCAL_FONT = PROJECT_ROOT / "assets" / "fonts" / "simhei.ttf"
FONT_PATH = str(LOCAL_FONT) if LOCAL_FONT.exists() else r"C:\Windows\Fonts\simhei.ttf"
# ==============================


def collect_lines():
    lines = []
    files = sorted(PROJECT_ROOT.rglob("*"))
    for p in files:
        if not p.is_file():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in CODE_EXTS:
            continue
        if p.name == Path(__file__).name:
            continue

        rel = p.relative_to(PROJECT_ROOT)
        lines.append(f"// ============ {rel} ============")
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                for raw in fp:
                    s = raw.rstrip("\n").rstrip()
                    if s == "":
                        continue
                    if s.lstrip().startswith("#"):
                        continue
                    if s.lstrip().startswith("//"):
                        continue
                    lines.append(s[:120])
        except Exception as e:
            print(f"跳过 {rel}：{e}")
    return [ln for ln in lines if ln.strip()]


def main():
    print(f"字体：{FONT_PATH}")
    lines = collect_lines()
    total_lines = len(lines)
    total_pages = (total_lines + LINES_PER_PAGE - 1) // LINES_PER_PAGE
    print(f"有效代码行数：{total_lines}")
    print(f"预计页数：{total_pages}")

    # 超过 60 页只留前 30 + 后 30
    if total_pages > 60:
        first = lines[: 30 * LINES_PER_PAGE]
        last = lines[-30 * LINES_PER_PAGE:]
        lines = first + ["// ......（中间省略）......"] + last
        total_pages = (len(lines) + LINES_PER_PAGE - 1) // LINES_PER_PAGE

    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_font("cn", fname=FONT_PATH)

    for page_num in range(total_pages):
        pdf.add_page()
        pdf.set_font("cn", size=9)
        pdf.cell(120, 6, f"{SOFTWARE_NAME} {VERSION}", ln=0, align="L")
        pdf.cell(0, 6, f"第 {page_num + 1} 页 共 {total_pages} 页", ln=1, align="R")
        pdf.ln(1)

        pdf.set_font("cn", size=7)
        start = page_num * LINES_PER_PAGE
        for line in lines[start:start + LINES_PER_PAGE]:
            pdf.cell(0, 4, line, ln=1)

    out = PROJECT_ROOT / f"{SOFTWARE_NAME}{VERSION}_源代码.pdf"
    pdf.output(str(out))
    print(f"已生成：{out}")


if __name__ == "__main__":
    main()