from pathlib import Path


def test_training_keeps_required_lineage_contract():
    source = (Path(__file__).parents[1] / "src/train.py").read_text()
    for required in (
        "source.git.commit",
        "dataset.version",
        "dataset_version",
        "macro_f1",
        "registered_model_name",
    ):
        assert required in source
