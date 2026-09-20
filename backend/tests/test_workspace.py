import pytest

from app.services.workspace import WorkspaceService


def test_workspace_rejects_traversal(tmp_path):
    service = WorkspaceService(str(tmp_path))
    service.create("job")
    with pytest.raises(ValueError):
        service.resolve_file("job", "../../outside.txt")
