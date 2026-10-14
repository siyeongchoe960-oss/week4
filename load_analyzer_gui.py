import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from load_analyzer import read_load_data


SECTION_INPUTS = {
    "사각형": [("폭 b", "width"), ("높이 h", "height")],
    "원형봉": [("지름 d", "diameter")],
    "원형관": [("외경 D", "outer_diameter"), ("두께 t", "thickness")],
    "사각형관": [
        ("외부 폭 B", "outer_width"),
        ("외부 높이 H", "outer_height"),
        ("두께 t", "thickness"),
    ],
    "H형강": [
        ("전체 높이 H", "height"),
        ("플랜지 폭 B", "flange_width"),
        ("웨브 두께 tw", "web_thickness"),
        ("플랜지 두께 tf", "flange_thickness"),
    ],
}


def calculate_area(section, dimensions):
    """단면 치수(mm)를 받아 단면적(mm²)을 계산하고 유효성을 검증한다."""
    if any(
        not math.isfinite(value) or value <= 0
        for value in dimensions.values()
    ):
        raise ValueError("모든 치수는 0보다 큰 유한한 숫자여야 합니다.")

    if section == "사각형":
        return dimensions["width"] * dimensions["height"]

    if section == "원형봉":
        diameter = dimensions["diameter"]
        return math.pi * diameter**2 / 4

    if section == "원형관":
        outer_diameter = dimensions["outer_diameter"]
        thickness = dimensions["thickness"]
        if 2 * thickness >= outer_diameter:
            raise ValueError("원형관은 2t가 외경 D보다 작아야 합니다.")
        inner_diameter = outer_diameter - 2 * thickness
        return math.pi * (
            outer_diameter**2 - inner_diameter**2
        ) / 4

    if section == "사각형관":
        outer_width = dimensions["outer_width"]
        outer_height = dimensions["outer_height"]
        thickness = dimensions["thickness"]
        if 2 * thickness >= min(outer_width, outer_height):
            raise ValueError("사각형관은 2t가 외부 폭 B와 높이 H보다 작아야 합니다.")
        return (
            outer_width * outer_height
            - (outer_width - 2 * thickness)
            * (outer_height - 2 * thickness)
        )

    if section == "H형강":
        flange_width = dimensions["flange_width"]
        height = dimensions["height"]
        flange_thickness = dimensions["flange_thickness"]
        web_thickness = dimensions["web_thickness"]
        if 2 * flange_thickness >= height:
            raise ValueError("H형강은 2tf가 높이 h보다 작아야 합니다.")
        if web_thickness >= flange_width:
            raise ValueError("H형강은 웨브 두께 tw가 플랜지 폭 b보다 작아야 합니다.")
        return (
            2 * flange_width * flange_thickness
            + (height - 2 * flange_thickness) * web_thickness
        )

    raise ValueError(f"지원하지 않는 단면 종류입니다: {section}")


class LoadAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Load Analyzer")
        self.root.geometry("850x700")

        self.data = []
        self.path_var = tk.StringVar()
        self.count_var = tk.StringVar(value="유효 데이터 수: -")
        self.section_var = tk.StringVar(value="사각형")
        self.dimension_vars = {}
        self.area_var = tk.StringVar(value="단면적 A: - mm²")
        self.result_var = tk.StringVar(value="최대 응력: -")

        top_frame = ttk.Frame(root, padding=10)
        top_frame.pack(fill="x")

        ttk.Button(
            top_frame,
            text="CSV 찾아보기",
            command=self.select_csv,
        ).pack(side="left")

        ttk.Entry(
            top_frame,
            textvariable=self.path_var,
            state="readonly",
        ).pack(side="left", padx=8, fill="x", expand=True)

        ttk.Label(
            root,
            textvariable=self.count_var,
            padding=(10, 0),
        ).pack(anchor="w")

        section_frame = ttk.LabelFrame(
            root,
            text="단면 설정",
            padding=10,
        )
        section_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(section_frame, text="단면 종류").grid(
            row=0, column=0, padx=5, pady=5
        )

        self.section_combo = ttk.Combobox(
            section_frame,
            textvariable=self.section_var,
            values=list(SECTION_INPUTS),
            state="readonly",
            width=12,
        )
        self.section_combo.grid(row=0, column=1, padx=5, pady=5)
        self.section_combo.bind("<<ComboboxSelected>>", self.change_section)

        self.dimension_frame = ttk.Frame(section_frame)
        self.dimension_frame.grid(row=1, column=0, columnspan=9, pady=5)

        ttk.Label(
            section_frame,
            textvariable=self.area_var,
        ).grid(row=2, column=0, columnspan=7, padx=10, pady=5, sticky="w")

        ttk.Button(
            section_frame,
            text="분석",
            command=self.analyze,
        ).grid(row=2, column=8, padx=10, pady=5)

        self.build_dimension_inputs()

        ttk.Label(
            root,
            textvariable=self.result_var,
            padding=(10, 0),
        ).pack(anchor="w")

        graph_frame = ttk.Frame(root, padding=10)
        graph_frame.pack(fill="both", expand=True)

        self.figure, self.axes = plt.subplots()
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Force (N)")
        self.axes.grid(True)

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=graph_frame,
        )
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()

    def change_section(self, _event=None):
        self.build_dimension_inputs()

    def build_dimension_inputs(self):
        for child in self.dimension_frame.winfo_children():
            child.destroy()

        self.dimension_vars = {}
        for column, (label_text, key) in enumerate(
            SECTION_INPUTS[self.section_var.get()]
        ):
            variable = tk.StringVar()
            variable.trace_add("write", self.update_area)
            self.dimension_vars[key] = variable
            ttk.Label(
                self.dimension_frame,
                text=f"{label_text} (mm)",
            ).grid(row=0, column=column * 2, padx=5, pady=5)
            ttk.Entry(
                self.dimension_frame,
                textvariable=variable,
                width=10,
            ).grid(row=0, column=column * 2 + 1, padx=5, pady=5)
        self.update_area()

    def select_csv(self):
        selected_path = filedialog.askopenfilename(
            title="CSV 파일 선택",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )

        if not selected_path:
            return

        self.data = []
        try:
            data, excluded_count = read_load_data(Path(selected_path))
        except (OSError, ValueError) as error:
            messagebox.showerror("CSV 읽기 오류", str(error))
            self.path_var.set("")
            self.count_var.set("유효 데이터 수: -")
            self.clear_graph()
            return

        self.path_var.set(selected_path)
        self.data = data
        self.count_var.set(
            f"유효 데이터 수: {len(self.data)}개 "
            f"(제외한 행 수: {excluded_count}개)"
        )
        self.result_var.set("최대 응력: -")
        self.clear_graph()

        if not self.data:
            messagebox.showwarning(
                "유효한 데이터 없음",
                "유효한 데이터가 없어 분석을 중단합니다.\n"
                "time_s와 force_N 열에 숫자 값이 있는지 확인하세요.",
            )

    def update_area(self, *_):
        try:
            dimensions = {
                key: float(variable.get())
                for key, variable in self.dimension_vars.items()
            }
            area = calculate_area(self.section_var.get(), dimensions)
            self.area_var.set(f"단면적 A: {area:.2f} mm²")
        except (TypeError, ValueError):
            self.area_var.set("단면적 A: - mm²")

    def analyze(self):
        if not self.data:
            messagebox.showwarning(
                "분석할 데이터 없음",
                "유효한 데이터가 없어 분석을 중단합니다.\n"
                "먼저 유효한 CSV 파일을 선택하세요.",
            )
            return

        try:
            dimensions = {
                key: float(variable.get())
                for key, variable in self.dimension_vars.items()
            }
            area = calculate_area(self.section_var.get(), dimensions)
        except (TypeError, ValueError) as error:
            messagebox.showerror(
                "입력 오류",
                str(error),
            )
            return

        stress_data = [
            (time_s, force_N / area)
            for time_s, force_N in self.data
        ]

        maximum_time, maximum_stress = max(
            stress_data,
            key=lambda item: item[1],
        )

        self.area_var.set(f"단면적 A: {area:.2f} mm²")
        self.result_var.set(
            f"최대 응력: {maximum_stress:.2f} MPa, "
            f"해당 시간: {maximum_time:.2f} s"
        )
        self.draw_stress_graph(stress_data)

    def clear_graph(self):
        self.axes.clear()
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Force (N)")
        self.axes.grid(True)
        self.canvas.draw()

    def draw_stress_graph(self, stress_data):
        self.axes.clear()

        time_values = [time_s for time_s, _ in stress_data]
        stress_values = [stress for _, stress in stress_data]

        self.axes.plot(
            time_values,
            stress_values,
            marker="o",
            linestyle="-",
        )

        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Stress (MPa)")
        self.axes.grid(True)

        self.figure.tight_layout()
        self.canvas.draw()


def main():
    root = tk.Tk()
    LoadAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()