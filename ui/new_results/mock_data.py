from .view_models import ActionEvaluationVM, StageVM, MetricVM, TrainingVM, FrameRef, VideoInfo

# Pure mock producer for quick preview (no core dependencies)

def build_mock_vm() -> ActionEvaluationVM:
    # Use real test video assets for frame extraction preview
    user_v = r'D:\\code\SportsMovementComparison\\tests\\experimental\\test_data\\me.mp4'
    std_v = r'D:\\code\SportsMovementComparison\\tests\\experimental\\test_data\\demo.mp4'
    stages = [
        StageVM(
            key='setup',
            name='Setup Phase',
            score=64,
            summary_raw='Stable ready posture but racket face slightly tilted back.',
            suggestion='Lower initial racket height and keep shoulders relaxed.',
            metrics=[
                MetricVM(key='elbow_angle', name='Elbow Angle', user_value=75, std_value=65, unit='°', deviation=10, status='warn'),
                MetricVM(key='shoulder_abduction', name='Shoulder Abduction', user_value=32, std_value=30, unit='°', deviation=2, status='ok'),
                MetricVM(key='center_height', name='Center Height', user_value=1.12, std_value=1.10, unit='m', deviation=0.02, status='ok'),
            ],
            user_frame=FrameRef(frame_index=60, video_path=user_v),
            standard_frame=FrameRef(frame_index=80, video_path=std_v)
        ),
        StageVM(
            key='backswing',
            name='Backswing Phase',
            score=78,
            summary_raw='Torso rotation range is appropriate.',
            suggestion='Keep core engaged and avoid lumbar collapse.',
            metrics=[
                MetricVM(key='trunk_rotation', name='Trunk Rotation', user_value=70, std_value=72, unit='°', deviation=-2, status='ok'),
                MetricVM(key='elbow_flex', name='Elbow Flexion', user_value=52, std_value=50, unit='°', deviation=2, status='ok'),
                MetricVM(key='backswing_width', name='Backswing Width', user_value=0.82, std_value=0.85, unit='m', deviation=-0.03, status='ok'),
            ],
            user_frame=FrameRef(frame_index=70, video_path=user_v),
            standard_frame=FrameRef(frame_index=90, video_path=std_v)
        ),
        StageVM(
            key='power',
            name='Power Phase',
            score=58,
            summary_raw='Forearm acceleration insufficient; hips opening too early.',
            suggestion='Delay hip opening sequence and strengthen forearm whip drills.',
            metrics=[
                MetricVM(key='hip_rotation_speed', name='Hip Rotation Speed', user_value=210, std_value=250, unit='°/s', deviation=-40, status='bad'),
                MetricVM(key='forearm_ang_acc', name='Forearm Angular Acc.', user_value=820, std_value=950, unit='°/s²', deviation=-130, status='warn'),
                MetricVM(key='impact_timing', name='Impact Timing', user_value=0.62, std_value=0.58, unit='s', deviation=0.04, status='warn'),
            ],
            user_frame=FrameRef(frame_index=80, video_path=user_v),
            standard_frame=FrameRef(frame_index=100, video_path=std_v)
        ),
    ]
    training = TrainingVM(
        key_issues=['Elbow angle too large', 'Insufficient forearm acceleration'],
        improvement_drills=['Wall swing drill', 'Tempo breakdown practice'],
        next_steps=['Add multi-shuttle drills', 'Improve core stability']
    )
    return ActionEvaluationVM(
    sport='Badminton',
    action_name='Forehand Clear',
        score=72,
    summary_raw='Player completed the full stroke sequence.',
    summary_refined='Your ready racket position is too high, reducing power efficiency.',
        stages=stages,
        training=training,
    video=VideoInfo(user_video_path=user_v, standard_video_path=std_v)
    )

__all__ = ['build_mock_vm']
