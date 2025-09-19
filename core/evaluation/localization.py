from __future__ import annotations
from typing import Dict

# Simple template storage. Real system could merge with existing localization infra.

MEASUREMENT_FEEDBACK = {
    'zh_CN': {
        'default_pass': '{desc}：良好。',
        'default_fail': '{desc}：需要改进 (当前 {value:.2f})。',
        'deviation_fail': '{desc} 偏差 {dev:.2f} (目标 {target:.2f}±{tol:.2f})。',
    },
    'en_US': {
        'default_pass': '{desc}: Good.',
        'default_fail': '{desc}: Needs improvement (current {value:.2f}).',
        'deviation_fail': '{desc} deviation {dev:.2f} (target {target:.2f}±{tol:.2f}).',
    }
}

STAGE_FEEDBACK = {
    'zh_CN': {
        'summary_good': '{stage}整体表现良好。',
        'summary_mixed': '{stage}存在部分指标需改进。',
        'summary_poor': '{stage}大部分指标不达标。',
    },
    'en_US': {
        'summary_good': '{stage} overall performance is good.',
        'summary_mixed': '{stage} has some metrics to improve.',
        'summary_poor': '{stage} most metrics below expectation.',
    }
}

ACTION_FEEDBACK = {
    'zh_CN': {
        'overall_good': '{action} 总体表现稳定。',
        'overall_mixed': '{action} 存在改进空间，关注关键阶段。',
        'overall_poor': '{action} 需重点调整多个阶段。',
    },
    'en_US': {
        'overall_good': '{action} overall stable performance.',
        'overall_mixed': '{action} some stages need attention.',
        'overall_poor': '{action} multiple stages need major adjustment.',
    }
}

DEFAULT_DESC = {
    'zh_CN': '指标',
    'en_US': 'Metric'
}

__all__ = [
    'MEASUREMENT_FEEDBACK', 'STAGE_FEEDBACK', 'ACTION_FEEDBACK', 'DEFAULT_DESC'
]
