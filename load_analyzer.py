"""load_data.csv의 하중 데이터를 분석하고 응력을 저장한다."""

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt



CSV_PATH = Path(__file__).with_name("load_bad.csv")
REFERENCE_STRESS_MPA = 6
RESULT_PATH = Path(__file__).with_name("load_result.csv")
PLOT_PATH = Path(__file__).with_name("stress_plot.png")
EXPECTED_FIELDS = ["time_s", "force_N"]
AREA_MM2 = 100


def read_load_data(csv_path):
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)

        fieldnames = reader.fieldnames or []
        missing_fields = [
            field for field in EXPECTED_FIELDS if field not in fieldnames
        ]
        if missing_fields:
            raise ValueError(
                "CSV에 필요한 열이 없습니다: "
                + ", ".join(missing_fields)
            )

        data = []
        excluded_count = 0

        for row_number, row in enumerate(reader, start=2):
            invalid = False
            values = {}

            for field in EXPECTED_FIELDS:
                raw_value = row.get(field)

                try:
                    if raw_value is None or not raw_value.strip():
                        raise ValueError
                    value = float(raw_value)
                    if not math.isfinite(value):
                        raise ValueError
                    values[field] = value
                except (AttributeError, ValueError):
                    print(
                        f"원본 CSV {row_number}행: "
                        f"{field} 문제값 = {raw_value!r}"
                    )
                    invalid = True

            if invalid:
                excluded_count += 1
                continue

            data.append((values["time_s"], values["force_N"]))

    return data, excluded_count


def write_load_result(result_path, data):
    with result_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["time_s", "force_N", "stress_MPa"])

        for time_s, force_N in data:
            writer.writerow([time_s, force_N, force_N / AREA_MM2])


def write_stress_plot(plot_path, data):
    time_values = [row[0] for row in data]
    stress_values = [row[1] / AREA_MM2 for row in data]

    max_index = stress_values.index(max(stress_values))
    max_time = time_values[max_index]
    max_stress = stress_values[max_index]

    fig, ax = plt.subplots()
    ax.plot(time_values, stress_values, marker="o", linestyle="-")
    ax.scatter(
        [max_time],
        [max_stress],
        color="red",
        s=80,
        zorder=3,
        label="Maximum stress",
    )
    ax.annotate(
        f"Time: {max_time:.2f} s\nStress: {max_stress:.2f} MPa",
        (max_time, max_stress),
        xytext=(8, 8),
        textcoords="offset points",
    )

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Stress (MPa)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)


def main():
    data, excluded_count = read_load_data(CSV_PATH)

    print(f"제외한 행 수: {excluded_count}개")
    print(f"유효한 데이터 수: {len(data)}개")

    if not data:
        print("유효한 데이터가 없어 계산을 중단합니다.")
        return

    maximum_time, maximum_force = max(data, key=lambda item: item[1])
    maximum_stress_time, maximum_stress = max(
        ((time_s, force_N / AREA_MM2) for time_s, force_N in data),
        key=lambda item: item[1],
    )

    exceeded_count = sum(
        force_N / AREA_MM2 > REFERENCE_STRESS_MPA
        for _, force_N in data
    )
    print(f"기준 응력 {REFERENCE_STRESS_MPA} MPa 초과 데이터 개수: {exceeded_count}개")

    write_load_result(RESULT_PATH, data)
    write_stress_plot(PLOT_PATH, data)

    print("데이터 개수: {}개".format(len(data)))
    print("최대하중: {} N".format(maximum_force))
    print("해당 시간: {} s".format(maximum_time))
    print("최대응력: {} MPa".format(maximum_stress))
    print("최대응력 해당 시간: {} s".format(maximum_stress_time))


if __name__ == "__main__":
    main()