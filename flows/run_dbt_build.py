import json
from os import getenv
import subprocess
import tempfile
from pathlib import Path

from prefect import flow, get_run_logger, task
from prefect.artifacts import create_markdown_artifact

from lib.config import ProjectConfig, get_config


def _profiles_yml_content(
    config: ProjectConfig, target: str, keyfile_path: Path
) -> str:
    return (
        "dbt_parlemAn:\n"
        f"  target: {target}\n"
        "  outputs:\n"
        f"    {target}:\n"
        "      type: bigquery\n"
        "      method: service-account\n"
        f"      project: {config.gcp_project}\n"
        f"      dataset: {config.bq_dataset}\n"
        "      threads: 4\n"
        "      timeout_seconds: 300\n"
        "      location: EU\n"
        f"      keyfile: {keyfile_path}\n"
    )


@task
def run_dbt_build(
    config: ProjectConfig,
    target: str = "prod",
    select: str | None = None,
    full_refresh: bool = False,
) -> None:
    logger = get_run_logger()

    project_dir = Path(__file__).resolve().parents[1] / "dbt_parlemAn"

    with tempfile.TemporaryDirectory(prefix="dbt_profiles_") as profiles_dir:
        keyfile_path = Path(profiles_dir) / "service_account.json"
        profiles_path = Path(profiles_dir) / "profiles.yml"

        keyfile_path.write_text(
            json.dumps(config.service_account_info), encoding="utf-8"
        )

        profiles_path.write_text(
            _profiles_yml_content(config, target, keyfile_path),
            encoding="utf-8",
        )

        command = f"dbt build --project-dir {project_dir} --profiles-dir {profiles_dir} --target {target}"

        if select:
            command += f" --select {select}"
        if full_refresh:
            command += " --full-refresh"

        logger.info("Running command: %s", command)
        result = subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
            shell=True,
            executable=getenv("SHELL", "/bin/bash"),
        )

    if result.stdout:
        logger.info("dbt stdout:\n%s", result.stdout)
    if result.stderr:
        logger.warning("dbt stderr:\n%s", result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"dbt build failed with exit code {result.returncode}")

    create_markdown_artifact(
        key="dbt-build-summary",
        markdown=(
            f"### dbt build succeeded\n"
            f"- target: `{target}`\n"
            f"- project: `{config.gcp_project}`\n"
            f"- dataset: `{config.bq_dataset}`\n"
            f"- select: `{select or 'all'}`\n"
            f"- full_refresh: `{full_refresh}`"
        ),
        description="dbt build execution summary",
    )


@flow
def dbt_build_flow(
    target: str = "prod",
    select: str | None = None,
    full_refresh: bool = False,
) -> None:
    config = get_config()
    run_dbt_build(
        config=config, target=target, select=select, full_refresh=full_refresh
    )


if __name__ == "__main__":
    dbt_build_flow()
