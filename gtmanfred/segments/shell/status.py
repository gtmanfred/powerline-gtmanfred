from powerline.theme import requires_segment_info
from powerline.segments import with_docstring

@requires_segment_info
def last_status(pl, segment_info):
        '''Return last exit code.
        Highlight groups used: ``exit_fail``
        '''
        if not segment_info['args'].last_exit_code:
            ret = '(⌐■_■)'
            return [{'contents': ret, 'highlight_groups': ['exit_success']}]
        return [
            {'contents': str(segment_info['args'].last_exit_code), 'highlight_groups': ['exit_code']},
            {'contents': '（╯°□°）╯︵ ┻━┻', 'highlight_groups': ['exit_fail']}
        ]
