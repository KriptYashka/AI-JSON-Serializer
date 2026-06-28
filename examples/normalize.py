import asyncio
import sys
from datetime import datetime
from pathlib import Path

from src.excel_reader import ai_detect_header_row, detect_header_row, read_headers
from src.pipeline import run_pipeline
from src.schema import Normalizer, load_schema


async def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python -m examples.normalize <input.xls/.xlsx> [--output <out.xlsx>] [--header-row <N>]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"Файл не найден: {input_path}")
        sys.exit(1)

    output_arg: str | None = None
    header_row: int | None = None

    args = sys.argv[2:]
    for i, a in enumerate(args):
        if a == "--output" and i + 1 < len(args):
            output_arg = args[i + 1]
        if a == "--header-row" and i + 1 < len(args):
            header_row = int(args[i + 1])

    schema = load_schema()

    if header_row is not None:
        print(f"Строка заголовков: {header_row} (явно)")
    else:
        print("Поиск строки заголовков…", end=" ")
        header_row = detect_header_row(input_path)
        print(f"найдена строка {header_row}")

    headers = read_headers(input_path, header_row=header_row)

    print(f"Заголовки: {headers}")
    print("Цепочка: дешёвая модель → дорогая проверка\n")

    mapping_rules = await run_pipeline(headers, schema)

    print("\nИтоговый маппинг:")
    for r in mapping_rules:
        print(f"  {r.from_} → {r.to}")

    output_path = Path(output_arg or f"normalized_{input_path.stem}_{datetime.now().strftime('%H%M%S')}.xlsx")
    normalizer = Normalizer(schema, mapping_rules)
    count = normalizer.normalize(input_path, output_path, header_row=header_row)
    print(f"\nГотово: {count} строк → {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
