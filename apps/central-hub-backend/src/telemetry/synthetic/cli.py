# apps/central-hub-backend/src/telemetry/synthetic/cli.py

import argparse
import sys
import os
import logging
from typing import List

# Resolve path relative to central-hub-backend root
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.telemetry.synthetic.config import GeneratorConfig
from src.telemetry.synthetic.generator import SyntheticTelemetryGenerator
from src.telemetry.synthetic.exporter import TelemetryExporter
from src.database.database import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("synthetic_telemetry_cli")

def main(args: List[str] = None) -> None:
    parser = argparse.ArgumentParser(description="Envoy AI Synthetic Telemetry Dataset Generator CLI")
    parser.add_argument("--total", type=int, default=1000, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Seed value for reproducibility")
    parser.add_argument("--days", type=int, default=30, help="Days of historical timestamps to cover")
    parser.add_argument("--error-rate", type=float, default=0.05, help="Failure rate percentage (0.0 to 1.0)")
    parser.add_argument("--use-llm", action="store_true", help="Utilize Groq LLM API for message strings")
    parser.add_argument("--export", type=str, default="json", choices=["json", "jsonl", "csv", "sql", "copy", "db"],
                        help="Export format target")
    parser.add_argument("--output", type=str, default=None,
                        help="Optional filepath path for saving outputs (not used for --export db)")

    parsed = parser.parse_args(args)

    # 1. Prepare configuration
    config = GeneratorConfig(
        total_conversations=parsed.total,
        random_seed=parsed.seed,
        date_range_days=parsed.days,
        error_rate=parsed.error_rate,
        use_llm=parsed.use_llm
    )

    # 2. Run generator
    generator = SyntheticTelemetryGenerator(config)
    data = generator.generate()

    # 3. Export
    export_format = parsed.export.lower()
    
    if export_format == "db":
        logger.info("Initiating database seed session...")
        db = SessionLocal()
        try:
            stats = TelemetryExporter.seed_database(data, db)
            logger.info("Database seeding successfully completed!")
            logger.info(f"Summary: {stats}")
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            db.rollback()
            sys.exit(1)
        finally:
            db.close()
            
    else:
        # Determine default output paths if not provided
        output_path = parsed.output
        if not output_path:
            ext_map = {"json": "json", "jsonl": "jsonl", "csv": "csv", "sql": "sql", "copy": "tsv"}
            output_path = f"synthetic_telemetry_{parsed.total}.{ext_map[export_format]}"
            
        logger.info(f"Exporting to {export_format.upper()} target: {output_path}...")
        
        try:
            if export_format == "json":
                TelemetryExporter.export_json(data, output_path)
            elif export_format == "jsonl":
                TelemetryExporter.export_jsonl(data, output_path)
            elif export_format == "csv":
                TelemetryExporter.export_csv(data, output_path)
            elif export_format == "sql":
                TelemetryExporter.export_sql(data, output_path)
            elif export_format == "copy":
                TelemetryExporter.export_copy(data, output_path)
                
            logger.info(f"Saved successfully to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export file: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
