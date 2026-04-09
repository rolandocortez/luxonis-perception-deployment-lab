# MVP Definition — Luxonis Perception Deployment & Reliability Lab

## Objective
Freeze the scope of the first working version of the project.

## MVP pipeline
Camera -> ImageManip -> DetectionNetwork -> ObjectTracker -> Output

## Allowed MVP variants

### Resolution
- 720p
- 1080p

### Resize mode
- crop
- letterbox
- stretch

### Tracker
- on
- off

### Confidence threshold
- 0.25
- 0.35
- 0.50

## Out of scope for MVP
- spatial detection
- stereo
- ROS2
- HubAI
- ModelConverter
- RVC deployment
- complex web dashboard

## MVP success criterion
A system that compares variants of a pipeline
Camera -> ImageManip -> DetectionNetwork -> ObjectTracker
and produces performance and visual stability metrics.