from __future__ import annotations
from .data_models import EvaluationState, StageResult, MetricValue, TrainingBundle, FrameRef
from ui.new_results.view_models import (
    ActionEvaluationVM, StageVM, MetricVM, TrainingVM, FrameRef as UIFrameRef, VideoInfo
)

class UIAdapter:
    @staticmethod
    def to_vm(state: EvaluationState, keyframes_user: dict, keyframes_std: dict) -> ActionEvaluationVM:
        stages_vm = []
        for sk, sr in state.stages.items():
            uf = keyframes_user.get(sk)
            sf = keyframes_std.get(sk)
            stages_vm.append(
                StageVM(
                    key=sr.stage_key,
                    name=sr.stage_key,
                    score=sr.score,
                    summary_raw=sr.summary or '',
                    suggestion=sr.suggestion or '',
                    metrics=[UIAdapter._metric_vm(m) for m in sr.metrics],
                    user_frame=UIAdapter._frame_vm(uf),
                    standard_frame=UIAdapter._frame_vm(sf)
                )
            )
        training_vm = None
        if state.training:
            training_vm = TrainingVM(
                key_issues=state.training.key_issues,
                improvement_drills=state.training.improvement_drills,
                next_steps=state.training.next_steps
            )
        return ActionEvaluationVM(
            sport=state.sport,
            action_name=state.action,
            score=state.overall_score or 0,
            summary_raw='自动生成的简要概览',
            summary_refined=None,
            stages=stages_vm,
            training=training_vm,
            video=VideoInfo(user_video_path=UIAdapter._video_path(keyframes_user), standard_video_path=UIAdapter._video_path(keyframes_std))
        )

    @staticmethod
    def _metric_vm(m: MetricValue) -> MetricVM:
        return MetricVM(
            key=m.key,
            name=m.name,
            user_value=m.user_value,
            std_value=m.std_value,
            unit=m.unit,
            deviation=m.deviation,
            status=m.status
        )

    @staticmethod
    def _frame_vm(fr: FrameRef | None):
        if not fr:
            return None
        return UIFrameRef(video_path=fr.video_path, frame_index=fr.frame_index)

    @staticmethod
    def _video_path(keyframes: dict) -> str:
        # pick any one frame's video path
        for fr in keyframes.values():
            return fr.video_path
        return ''

__all__ = ['UIAdapter']
