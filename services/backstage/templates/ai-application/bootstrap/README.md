# ${{ values.repoName }}

${{ values.description }}

This repository is being provisioned by Backstage. Main initially contains only
repository governance and catalog metadata. Application/deployment code arrives
in a separate pull request after required review protection has been verified.

Reviewer: @${{ values.reviewer }}. Accept the private repository invitation first.
Do not add code directly to main. If provisioning failed, inspect the Backstage
task before using this repository; a failed protection step means it is not ready.
