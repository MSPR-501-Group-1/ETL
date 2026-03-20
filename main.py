import sys
import argparse
import warnings
warnings.filterwarnings('ignore')

from services.pipeline_runner import list_pipelines, run_pipeline

def main():
    available = list_pipelines()

    parser = argparse.ArgumentParser(
        description="HealthAI Coach ETL — run one pipeline."
    )
    parser.add_argument(
        "pipeline",
        metavar="PIPELINE",
        help=(
            f"Pipeline to run: {', '.join(available)}."
        ),
    )
    args = parser.parse_args()

    success = run_pipeline(args.pipeline)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
