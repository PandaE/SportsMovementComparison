# New Evaluation Core (Prototype)

Purpose: Provide an incremental evaluation orchestration layer feeding UI view models.

## Components
- data_models.py: Domain dataclasses (config, results, keyframes)
- session.py: `EvaluationSession` orchestrator (dirty tracking, evaluation, events)
- adapter.py: Convert `EvaluationState` -> existing `ActionEvaluationVM`

## Quick Start
```python
from core.new_evaluation.data_models import ActionConfig, StageConfig, MetricConfig, KeyframeSet, FrameRef, ScoringPolicy
from core.new_evaluation.session import EvaluationSession
from core.new_evaluation.adapter import UIAdapter

config = ActionConfig(
    sport='badminton',
    action='forehand_clear',
    stages=[
        StageConfig(key='setup', name='准备', metrics=[MetricConfig(key='elbow_angle', name='肘角', target=65, warn_threshold=8)]),
        StageConfig(key='power', name='发力', metrics=[MetricConfig(key='trunk_rotation', name='躯干旋转', target=70, warn_threshold=5)])
    ],
    scoring=ScoringPolicy(stage_weights={'setup':0.4,'power':0.6})
)

keyframes = KeyframeSet(
    user={'setup': FrameRef('user.mp4',60), 'power': FrameRef('user.mp4',80)},
    standard={'setup': FrameRef('std.mp4',80), 'power': FrameRef('std.mp4',100)}
)

session = EvaluationSession(config, keyframes, user_video='user.mp4', standard_video='std.mp4')

session.on('stage_completed', lambda r: print('Stage done', r.stage_key, r.score))
session.on('action_completed', lambda st: print('All done overall', st.overall_score))

session.evaluate()  # full run
state = session.get_state()
vm = UIAdapter.to_vm(state, keyframes.user, keyframes.standard)
```

## Event Names
- `keyframe_updated(stage_key, frame_index)`
- `stage_completed(StageResult)`
- `action_completed(EvaluationState)`

## Next Steps
- Integrate real metrics_engine / comparison_engine
- Pose / feature extraction service injection
- Per-metric formula mapping registry
- Error propagation model
- Threaded evaluation for UI responsiveness

---
Prototype only: scoring & metric values are placeholder heuristics until engines are wired.
