import re
from uuid import UUID

from app.dispatch_ids import make_rq_job_id


def test_rq_id_uses_supported_characters_and_is_unique_per_dispatch():
    job_id = UUID("c0e16acd-0584-471f-a877-a68bbfe0c00a")
    first = make_rq_job_id(job_id)
    second = make_rq_job_id(job_id)
    assert first != second
    assert first.startswith("deployment-" + str(job_id) + "-")
    assert re.fullmatch(r"[A-Za-z0-9_-]+", first)
