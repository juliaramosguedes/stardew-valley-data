"""
run_all.py — executa todos os scrapers e gera os JSONs em data/

Uso:
    python scrapers/run_all.py
    python scrapers/run_all.py --only crops events
"""

import sys
import time
import argparse
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

SCRAPERS = {
    "crops": ("crops", "scrape"),
    "events": ("events", "scrape"),
    "community_center": ("community_center", "scrape"),
}


def run(name: str, module_name: str, func_name: str) -> bool:
    print(f"\n{'='*50}")
    print(f"  {name.upper()}")
    print(f"{'='*50}")
    try:
        import importlib
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)

        from base import validate_and_save
        data = func()
        validate_and_save(f"{name}.json", data, name)
        return True
    except Exception as e:
        print(f"[ERRO] {name}: {e}")
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="+", choices=list(SCRAPERS.keys()),
                        help="Executar apenas scrapers específicos")
    args = parser.parse_args()

    targets = args.only if args.only else list(SCRAPERS.keys())

    start = time.time()
    results = {}

    for name in targets:
        module_name, func_name = SCRAPERS[name]
        results[name] = run(name, module_name, func_name)

    elapsed = time.time() - start

    print(f"\n{'='*50}")
    print(f"  RESULTADO ({elapsed:.1f}s)")
    print(f"{'='*50}")
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")

    failed = [n for n, ok in results.items() if not ok]
    if failed:
        print(f"\n[WARN] Falhou: {', '.join(failed)}")
        sys.exit(1)
    else:
        print(f"\n[OK] Todos os dados gerados em data/")


if __name__ == "__main__":
    main()
