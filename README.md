## CSV 하중 분석 프로그램

`load_analyzer.py`는 `load_bad.csv`의 하중 데이터를 분석하고 응력을 계산합니다.

### 입력 파일

입력 파일명은 `load_bad.csv`이며, 다음 열을 포함해야 합니다.

| 열 이름 | 단위 | 설명 |
|---|---|---|
| `time_s` | s | 시간 |
| `force_N` | N | 하중 |

응력은 다음 식으로 계산합니다.

```text
stress_MPa = force_N / AREA_MM2
```

현재 단면적 설정은 `100 mm²`입니다. 변경하려면 `load_analyzer.py`의 `AREA_MM2` 값을 수정합니다.

### 필요한 라이브러리

- Python 표준 라이브러리: `csv`, `math`, `pathlib`
- 외부 라이브러리: `matplotlib`

설치 명령:

```powershell
python -m pip install matplotlib
```

### 실행 방법

```powershell
python load_analyzer.py
```

### 출력 파일

- `load_result.csv`: 유효한 데이터의 시간, 하중, 응력
- `stress_plot.png`: 시간–응력 그래프
  - x축: `Time (s)`
  - y축: `Stress (MPa)`
  - 각 데이터는 점과 선으로 표시
  - 최대응력점에 시간과 응력 표시

또한 기준 응력 `6 MPa`를 초과한 데이터 개수를 출력합니다.

### 오류 처리 규칙

- `time_s` 또는 `force_N`이 빈 값이거나 숫자가 아니면 해당 행을 제외합니다.
- 무한대와 NaN 값도 잘못된 값으로 처리합니다.
- 제외된 행의 원본 CSV 행 번호와 문제 값을 출력합니다.
- 제외한 행 수와 유효한 데이터 수를 출력합니다.
- 유효한 데이터가 없으면 계산과 파일 생성을 중단합니다.
- 원본 `load_bad.csv`는 수정하지 않습니다.