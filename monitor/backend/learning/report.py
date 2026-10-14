from learning.checks import count_views
from learning.report_support import assemble_report


def build_report(events, threshold=10):
    count = count_views(events)
    return assemble_report(events, count, threshold)
