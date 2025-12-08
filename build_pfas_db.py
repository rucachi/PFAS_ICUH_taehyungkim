from pathlib import Path

import pandas as pd
import sqlite3


# 1. CSV 폴더 / DB 저장 경로
DATA_DIR = Path(r"C:\Users\USER\Desktop\dimspec-main\dimspec-main\data")
OUTPUT_DB = Path(r"C:\Users\USER\Desktop\dimspec-main\dimspec-main\pfas_dimspec.db")


# 2. 실제 있는 CSV 파일 이름
FILES = {
    "ms1": "ms1s.csv",
    "peakid": "pfas_ms_intrelpeakid.csv",
    "scantime": "pfas_ms_intrelscantime.csv",
}


def try_load_csv(label: str, filename: str) -> pd.DataFrame | None:
    """지정된 CSV 파일을 시도해서 로드하고, 없으면 건너뜀."""
    filepath = DATA_DIR / filename

    if not filepath.exists():
        print(f"▶ 파일 없음: {filename} → 건너뜀")
        return None

    print(f"▶ 파일 로딩: {filename}")
    # 인코딩 문제 생기면 encoding="cp949" 로 바꿔볼 것
    return pd.read_csv(filepath, encoding="utf-8")


def main() -> None:
    print("▶ CSV 파일 로딩 시작")

    ms1 = try_load_csv("ms1", FILES["ms1"])
    peakid = try_load_csv("peakid", FILES["peakid"])
    scantime = try_load_csv("scantime", FILES["scantime"])

    print("▶ SQLite DB 생성 중…")
    OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(OUTPUT_DB) as conn:
        # 3. 각 CSV를 테이블로 저장
        if ms1 is not None:
            ms1.to_sql("ms1_raw", conn, if_exists="replace", index=False)

        if scantime is not None:
            scantime.to_sql("ms1_scantime", conn, if_exists="replace", index=False)

        if peakid is not None:
            peakid.to_sql("ms1_peak", conn, if_exists="replace", index=False)

            # PFAS별 요약 테이블 생성
            summary = (
                peakid.groupby(["pfas", "name", "precursor_mz"])
                .agg(
                    rt_mean=("scantime", "mean"),
                    rt_min=("scantime", "min"),
                    rt_max=("scantime", "max"),
                    n_points=("scantime", "size"),
                    n_peaks=("peak_id", "nunique"),
                )
                .reset_index()
            )
            summary.to_sql("pfas_summary", conn, if_exists="replace", index=False)

    print("완료:", OUTPUT_DB.resolve())


if __name__ == "__main__":
    main()

