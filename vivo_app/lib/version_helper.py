"""Builds status information for the standard version endpoint."""

import datetime
import logging
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest

logger = logging.getLogger(__name__)


def make_context(
    request: HttpRequest,
    request_started: datetime.datetime,
    version_text: str,
) -> dict[str, dict[str, str]]:
    """
    Assembles version information in the standard application response shape.

    Called by: views.version()
    """
    request_host: str = request.META.get('HTTP_HOST', '127.0.0.1')
    request_path: str = request.META.get('REQUEST_URI', request.META['PATH_INFO'])
    context: dict[str, dict[str, str]] = {
        'request': {
            'url': f'{request.scheme}://{request_host}{request_path}',
            'timestamp': str(request_started),
        },
        'response': {
            'ip': request.META.get('REMOTE_ADDR', 'unknown'),
            'version': version_text,
            'timetaken': str(datetime.datetime.now(tz=request_started.tzinfo) - request_started),
        },
    }
    return context


class GatherCommitAndBranchData:
    """Reads Git branch and commit metadata."""

    def __init__(self) -> None:
        self.commit: str = ''
        self.branch: str = ''

    def gather(self) -> None:
        """
        Gathers the branch and commit without calling Git.

        Called by: views.version()
        """
        head_text: str = self._read_head()
        self.commit = self._commit_from_head(head_text)
        self.branch = self._branch_from_head(head_text)
        logger.debug('branch, ``%s``; commit, ``%s``', self.branch, self.commit)

    def _read_head(self) -> str:
        """
        Reads the repository HEAD value, including from a Git worktree.

        Called by: GatherCommitAndBranchData.gather()
        """
        head_text: str = ''
        try:
            head_text = (self._git_directory() / 'HEAD').read_text(encoding='utf-8').strip()
        except FileNotFoundError:
            logger.error('no .git directory or HEAD file found')
        except OSError:
            logger.exception('problem reading the Git HEAD file')
        return head_text

    def _git_directory(self) -> Path:
        """
        Resolves the Git metadata directory for a checkout or worktree.

        Called by: GatherCommitAndBranchData._read_head(), GatherCommitAndBranchData._commit_from_head()
        """
        git_marker: Path = Path(settings.BASE_DIR) / '.git'
        git_directory: Path = git_marker
        if git_marker.is_file():
            marker_text: str = git_marker.read_text(encoding='utf-8').strip()
            prefix: str = 'gitdir:'
            if marker_text.startswith(prefix):
                configured_path = Path(marker_text.removeprefix(prefix).strip())
                if not configured_path.is_absolute():
                    configured_path = git_marker.parent / configured_path
                git_directory = configured_path.resolve()
        return git_directory

    def _commit_from_head(self, head_text: str) -> str:
        """
        Gets the commit hash named by HEAD, including a packed reference.

        Called by: GatherCommitAndBranchData.gather()
        """
        commit: str = 'commit_not_found'
        try:
            if head_text.startswith('ref:'):
                ref_path: str = head_text.split(maxsplit=1)[1]
                git_directory: Path = self._git_directory()
                commit_file: Path = git_directory / ref_path
                if commit_file.exists():
                    commit = commit_file.read_text(encoding='utf-8').strip()
                else:
                    commit = self._read_packed_ref(git_directory, ref_path)
            elif head_text:
                commit = head_text
        except (FileNotFoundError, IndexError):
            logger.error('Git commit reference was not found')
        except OSError:
            logger.exception('problem reading the Git commit reference')
        return commit

    def _read_packed_ref(self, git_directory: Path, ref_path: str) -> str:
        """
        Reads a commit from packed-refs when no loose reference exists.

        Called by: GatherCommitAndBranchData._commit_from_head()
        """
        commit: str = 'commit_not_found'
        packed_refs: Path = git_directory / 'packed-refs'
        for line in packed_refs.read_text(encoding='utf-8').splitlines():
            if line.startswith(('#', '^')):
                continue
            fields: list[str] = line.split(maxsplit=1)
            if len(fields) == 2 and fields[1] == ref_path:
                commit = fields[0]
                break
        return commit

    def _branch_from_head(self, head_text: str) -> str:
        """
        Gets the branch name from HEAD or reports a detached checkout.

        Called by: GatherCommitAndBranchData.gather()
        """
        branch: str = 'branch_not_found'
        if head_text.startswith('ref:'):
            ref_path: str = head_text.split(maxsplit=1)[1]
            branch = ref_path.split('/')[-1]
        elif head_text:
            branch = 'detached'
        return branch


_loaded_gatherer = GatherCommitAndBranchData()
_loaded_gatherer.gather()
LOADED_VERSION = f'{_loaded_gatherer.branch} {_loaded_gatherer.commit}'
