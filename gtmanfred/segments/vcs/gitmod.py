# vim:fileencoding=utf-8:et
import os
from git import Repo, GitCommandError, InvalidGitRepositoryError
from powerline.segments import Segment, with_docstring
from powerline.theme import requires_segment_info


@requires_segment_info
class GitStatusSegment(Segment):
    def _map_gitdir(self, gfile):
        return os.path.join(self.repo.git_dir, gfile)

    @property
    def _action(self):
        for checkdir in map(self._map_gitdir, ["rebase-apply", "rebase", "../.dotest"]):
            if os.path.isdir(checkdir):
                if os.path.isfile(os.path.join(checkdir, 'rebasing')):
                    return 'rebase'
                elif os.path.isfile(os.path.join(checkdir, 'applying')):
                    return 'am'
                else:
                    return "am/rebase" 

        for checkfile in map(self._map_gitdir, ["rebase-merge/interactive", ".dotest-merge/interactive"]):
            if os.path.isfile(checkfile):
                return "rebase-i"

        for checkdir in map(self._map_gitdir, ["rebase-merge", ".dotest-merge"]):
            if os.path.isdir(checkdir):
                return "rebase-m"

        if os.path.isfile(self._map_gitdir('MERGE_HEAD')):
            return "merge"

        if os.path.isfile(self._map_gitdir('BISECT_LOG')):
            return "bisect"
        if os.path.isfile(self._map_gitdir('CHERRY_PICK_HEAD')):
            if os.path.isdir(self._map_gitdir('sequencer')):
                return "cherry-seq"
            else:
                return "cherry"
        if os.path.isdir(self._map_gitdir('sequencer')):
            return "cherry-or-revert"
        return ""

    @property
    def _branch(self):
        for checkdir in map(self._map_gitdir, ["rebase-apply", "rebase", "../.dotest"]):
            if os.path.isdir(checkdir):
                actiondir = checkdir
                if not self.repo.head.is_detached:
                    return self.repo.head.ref.name
                with open(os.path.join(checkdir, 'head-name'), 'r') as headfile:
                    return headfile.read().split()

        if os.path.isfile(self._map_gitdir('MERGE_HEAD')):
            with open(self._map_gitdir('MERGE_HEAD'), 'r') as headfile:
                return headfile.read().strip()

        if os.path.isdir(self._map_gitdir('rebase-merge')):
            with open(os.path.join(self._map_gitdir('rebase-merge'), 'head-name'), 'r') as headfile:
                return headfile.read().strip()

        if os.path.isdir(self._map_gitdir('.dotest-merge')):
            with open(os.path.join(self._map_gitdir('.dotest-merge'), 'head-name'), 'r') as headfile:
                return headfile.read().strip()

        if not self.repo.head.is_detached:
            return self.repo.head.ref.name

        try:
            return 'refs/tags/{0}'.format(self.repo.git.describe('HEAD', all=True, exact_match=True))
        except GitCommandError:
            return self.repo.git.rev_parse('HEAD', short=True)

    def update_index(self):
        try:
            self.repo.git.update_index(q=True, ignore_submodules=True, refresh=True)
        except GitCommandError:
            pass

    @property
    def _staged(self):
        self.update_index()
        try:
            self.repo.git.diff_index('HEAD', cached=True, quiet=True, ignore_submodules=True)
            return False
        except GitCommandError:
            return True

    @property
    def _unstaged(self):
        self.update_index()
        try:
            self.repo.git.diff_files(quiet=True, ignore_submodules=True)
            return False
        except GitCommandError:
            return True

    @property
    def _untracked(self):
        return bool(self.repo.untracked_files)

    @property
    def _stashed(self):
        return len(filter(lambda x: x, self.repo.git.stash('list').split('\n')))

    def __call__(self, pl, segment_info, use_dash_c=True):
        pl.debug('Running gitstatus')
        cwd = segment_info['getcwd']()
        if not cwd:
            return
        try:
            self.repo = Repo(cwd)
        except InvalidGitRepositoryError:
            return

        return self.build_segments()

    def build_segments(self):
            if self._action:
                branch_group = 'gitstatus_branch_action'
            elif self.repo.head.is_detached:
                branch_group = 'gitstatus_branch_detached'
            elif self._staged or self._unstaged or self._untracked:
                branch_group = 'gitstatus_branch_dirty'
            else:
                branch_group = 'gitstatus_branch_clean'

            if self._action:
                segments = [
                    {
                        'contents': '{0}|{1}'.format(
                            self._branch,
                            self._action
                        ),
                        'highlight_groups': [
                            branch_group,
                            'gitstatus_branch',
                            'gitstatus'
                        ],
                        'divider_highlight_group': 'gitstatus:divider'
                    }
                ]
            else:
                segments = [
                    {
                        'contents': self._branch,
                        'highlight_groups': [
                            branch_group,
                            'gitstatus_branch',
                            'gitstatus'
                        ],
                        'divider_highlight_group': 'gitstatus:divider'
                    }
                ]

            if self._staged:
                segments.append({'contents': '●', 'highlight_groups': ['gitstatus_staged', 'gitstatus'], 'divider_highlight_group': 'gitstatus:divider'})
            if self._unstaged:
                segments.append({'contents': '!', 'highlight_groups': ['gitstatus_changed', 'gitstatus'], 'divider_highlight_group': 'gitstatus:divider'})
            if self._untracked:
                segments.append({'contents': '?', 'highlight_groups': ['gitstatus_untracked', 'gitstatus'], 'divider_highlight_group': 'gitstatus:divider'})
            if self._stashed:
                segments.append({'contents': ' ⚑ {0}'.format(self._stashed), 'highlight_groups': ['gitstatus_stashed', 'gitstatus'], 'divider_highlight_group': 'gitstatus:divider'})

            return segments

gitstatus = with_docstring(GitStatusSegment(),
'''Return the status of a Git working copy.
Divider highlight group used: ``gitstatus:divider``.
Highlight groups used: ``gitstatus_branch_detached``, ``gitstatus_branch_dirty``, ``gitstatus_branch_clean``, ``gitstatus_branch``, ``gitstatus_behind``, ``gitstatus_ahead``, ``gitstatus_staged``, ``gitstatus_unmerged``, ``gitstatus_changed``, ``gitstatus_untracked``, ``gitstatus_stashed``, ``gitstatus``.
''')
