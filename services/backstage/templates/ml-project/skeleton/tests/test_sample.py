import csv
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_is_balanced_and_contains_no_customer_identifiers(tmp_path):
    generator = load_module("generator", "src/generate_data.py")
    ninety = 90
    records = generator.generate(ninety)
    assert len(records) == ninety
    labels = {record["label"] for record in records}
    assert labels == set(generator.CLASSES)
    assert all(record["transaction_id"].startswith("MOCK-") for record in records)
    forbidden = {"customer_name", "email", "address", "taxpayer_id"}
    assert not forbidden.intersection(records[0])


def test_generated_csv_matches_training_contract(tmp_path):
    generator = load_module("generator2", "src/generate_data.py")
    output = tmp_path / "data.csv"
    records = generator.generate(60)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)
    trainer = load_module("trainer", "src/train.py")
    frame = trainer.load_dataset(output)
    model = trainer.build_pipeline()
    features = frame.drop(columns=["label", "transaction_id"])
    model.fit(features, frame["label"])
    assert len(model.predict(features.head(3))) == 3


def test_training_publishes_platform_lineage_contract():
    source = (ROOT / "src/train.py").read_text()
    for required in (
        "dataset-version", "source-git-commit", "registered_model_version",
        "macro_f1", "dataset.version", "source.git.commit",
    ):
        assert required in source
