"""
CLI: transforma JSONs de feedback de triagem para o formato de importação do software.
A lógica principal está em triagem_feedback_transformacao_json_para_importacao_intimacoes_service.py
"""
import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.triagem_feedback_transformacao_json_para_importacao_intimacoes_service import (
    run_batch,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transforma JSONs de feedback de triagem para o formato de "
            "importação do software de análise."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("feedbacksEntrada"),
        help="Diretório com arquivos JSON de entrada.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("feedbacksSaida"),
        help="Diretório para salvar os arquivos JSON transformados.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_batch(args.input_dir, args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
