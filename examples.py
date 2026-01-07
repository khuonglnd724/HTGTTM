"""
Advanced example usage of Lane Violation Detection System
Shows various use cases and customization options
"""

import cv2
import numpy as np
from pathlib import Path
from src.pipeline import LaneViolationPipeline
from src.utils.logger import Logger
from src.utils.analytics import AnalyticsCollector
from src.utils.drawing import DrawingUtils


def example_basic_video_processing():
    """Example 1: Basic video processing"""
    print("\n" + "="*60)
    print("Example 1: Basic Video Processing")
    print("="*60)
    
    # Initialize pipeline with default config
    pipeline = LaneViolationPipeline("configs/config.yaml")
    
    # Process video
    print("Processing video...")
    pipeline.run()
    
    print(f"Total violations detected: {pipeline.violation_count}")


def example_image_processing():
    """Example 2: Process single image"""
    print("\n" + "="*60)
    print("Example 2: Image Processing")
    print("="*60)
    
    pipeline = LaneViolationPipeline("configs/config.yaml")
    
    image_path = "data/videos/sample_frame.jpg"
    if Path(image_path).exists():
        result = pipeline.process_image(image_path, "data/outputs/result.jpg")
        print(f"Image processed and saved to: data/outputs/result.jpg")
    else:
        print(f"Image not found: {image_path}")


def example_custom_configuration():
    """Example 3: Use custom configuration"""
    print("\n" + "="*60)
    print("Example 3: Custom Configuration")
    print("="*60)
    
    pipeline = LaneViolationPipeline("configs/config.yaml")
    
    # Override configuration dynamically
    pipeline.config.set('yolo.model_name', 'yolov8l')  # Larger model
    pipeline.config.set('yolo.confidence_threshold', 0.4)  # Lower threshold
    pipeline.config.set('processing.frame_skip', 2)  # Process every 2nd frame
    
    print("Configuration updated:")
    print(f"  Model: {pipeline.config.get('yolo.model_name')}")
    print(f"  Confidence: {pipeline.config.get('yolo.confidence_threshold')}")
    print(f"  Frame Skip: {pipeline.config.get('processing.frame_skip')}")


def example_frame_by_frame_processing():
    """Example 4: Process video frame by frame with custom handling"""
    print("\n" + "="*60)
    print("Example 4: Frame-by-Frame Processing")
    print("="*60)
    
    pipeline = LaneViolationPipeline("configs/config.yaml")
    
    # Override video source
    pipeline.video_processor.input_source = "data/videos/sample.mp4"
    pipeline.video_processor.output_path = "data/outputs/custom_result.mp4"
    
    frame_count = 0
    violation_frames = []
    
    print("Processing frames...")
    
    while True:
        frame = pipeline.video_processor.read_frame()
        if frame is None:
            break
        
        # Process frame
        results = pipeline.process_frame(frame, frame_count)
        annotated = pipeline.draw_results(frame, results)
        
        # Write to output
        pipeline.video_processor.write_frame(annotated)
        
        # Track violations
        violations = results.get('violations', [])
        if any(v['is_violating'] for v in violations):
            violation_frames.append(frame_count)
        
        frame_count += 1
        
        if frame_count % 30 == 0:
            print(f"  Processed {frame_count} frames...")
    
    pipeline.video_processor.release()
    
    print(f"Total frames: {frame_count}")
    print(f"Frames with violations: {len(violation_frames)}")
    print(f"Output saved to: {pipeline.video_processor.output_path}")


def example_webcam_processing():
    """Example 5: Real-time webcam processing"""
    print("\n" + "="*60)
    print("Example 5: Webcam Real-time Processing")
    print("="*60)
    
    pipeline = LaneViolationPipeline("configs/config.yaml")
    
    # Use webcam (camera index 0)
    pipeline.video_processor.input_source = 0
    pipeline.video_processor.output_path = "data/outputs/webcam_result.mp4"
    
    print("Starting webcam. Press 'q' to quit.")
    
    frame_count = 0
    
    try:
        while True:
            frame = pipeline.video_processor.read_frame()
            if frame is None:
                break
            
            # Process frame
            results = pipeline.process_frame(frame, frame_count)
            annotated = pipeline.draw_results(frame, results)
            
            # Write to output
            pipeline.video_processor.write_frame(annotated)
            
            # Display frame
            cv2.imshow('Lane Violation Detection', annotated)
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            frame_count += 1
    
    finally:
        cv2.destroyAllWindows()
        pipeline.video_processor.release()
        print(f"Processed {frame_count} frames")


def example_with_analytics():
    """Example 6: Processing with detailed analytics"""
    print("\n" + "="*60)
    print("Example 6: Processing with Analytics")
    print("="*60)
    
    pipeline = LaneViolationPipeline("configs/config.yaml")
    analytics = AnalyticsCollector()
    
    # Start timing
    analytics.start_timing()
    
    frame_count = 0
    
    print("Processing with analytics collection...")
    
    while True:
        frame = pipeline.video_processor.read_frame()
        if frame is None:
            break
        
        # Process frame
        results = pipeline.process_frame(frame, frame_count)
        annotated = pipeline.draw_results(frame, results)
        
        # Write to output
        pipeline.video_processor.write_frame(annotated)
        
        # Collect analytics
        num_detections = len(results['detections'])
        violations = results.get('violations', [])
        num_violations = len([v for v in violations if v['is_violating']])
        
        analytics.record_frame_data(frame_count, num_detections, num_violations)
        
        # Record individual violations
        for violation in violations:
            if violation['is_violating']:
                analytics.record_violation(violation['track_id'])
        
        frame_count += 1
        
        if frame_count % 50 == 0:
            print(f"  Processed {frame_count} frames...")
    
    # End timing and print report
    analytics.end_timing()
    analytics.print_report()
    
    # Save report
    analytics.save_report("data/outputs/analytics_report.json")
    print(f"Analytics report saved to: data/outputs/analytics_report.json")
    
    pipeline.video_processor.release()


def example_custom_drawing():
    """Example 7: Custom visualization"""
    print("\n" + "="*60)
    print("Example 7: Custom Drawing and Visualization")
    print("="*60)
    
    # Create dummy image
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    img[:] = (255, 255, 255)  # White background
    
    # Draw examples
    DrawingUtils.draw_text(img, "Lane Violation Detection", (50, 50), 
                          color='blue', bg_color='white')
    
    # Draw boxes
    DrawingUtils.draw_box(img, (100, 200, 300, 400), color='green', 
                         label='Vehicle', confidence=0.95)
    
    # Draw lines (lane boundaries)
    DrawingUtils.draw_lines(img, [(400, 0, 400, 720), (800, 0, 800, 720)],
                           color='yellow')
    
    # Draw polygon
    polygon_points = [(600, 100), (800, 100), (900, 300), (500, 300)]
    DrawingUtils.draw_polygon(img, polygon_points, color='blue', 
                            fill=True, alpha=0.3)
    
    # Draw alert
    DrawingUtils.draw_alert_box(img, (1000, 500, 1100, 600), 
                               message="VIOLATION!")
    
    # Save
    cv2.imwrite("data/outputs/custom_drawing_example.jpg", img)
    print("Example drawing saved to: data/outputs/custom_drawing_example.jpg")


def example_batch_processing():
    """Example 8: Batch process multiple videos"""
    print("\n" + "="*60)
    print("Example 8: Batch Processing Multiple Videos")
    print("="*60)
    
    video_dir = Path("data/videos")
    video_files = list(video_dir.glob("*.mp4"))
    
    if not video_files:
        print("No MP4 files found in data/videos/")
        return
    
    print(f"Found {len(video_files)} videos to process")
    
    total_violations = 0
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n  Processing {i}/{len(video_files)}: {video_file.name}")
        
        pipeline = LaneViolationPipeline("configs/config.yaml")
        
        output_file = f"data/outputs/{video_file.stem}_result.mp4"
        pipeline.video_processor.input_source = str(video_file)
        pipeline.video_processor.output_path = output_file
        
        try:
            pipeline.run()
            total_violations += pipeline.violation_count
            print(f"  ✓ Completed: {output_file}")
        except Exception as e:
            print(f"  ✗ Error processing {video_file.name}: {str(e)}")
    
    print(f"\nBatch processing completed!")
    print(f"Total violations across all videos: {total_violations}")


def example_performance_comparison():
    """Example 9: Compare different models"""
    print("\n" + "="*60)
    print("Example 9: Model Performance Comparison")
    print("="*60)
    
    models = ['yolov8n', 'yolov8s', 'yolov8m']
    video_path = "data/videos/sample.mp4"
    
    if not Path(video_path).exists():
        print(f"Sample video not found: {video_path}")
        return
    
    results = {}
    
    for model in models:
        print(f"\nTesting model: {model}")
        
        pipeline = LaneViolationPipeline("configs/config.yaml")
        pipeline.config.set('yolo.model_name', model)
        
        analytics = AnalyticsCollector()
        analytics.start_timing()
        
        frame_count = 0
        while True:
            frame = pipeline.video_processor.read_frame()
            if frame is None:
                break
            
            results_frame = pipeline.process_frame(frame, frame_count)
            frame_count += 1
            
            if frame_count >= 100:  # Test on first 100 frames
                break
        
        analytics.end_timing()
        duration = analytics.get_duration()
        fps = frame_count / duration if duration > 0 else 0
        
        results[model] = {
            'frames': frame_count,
            'duration': duration,
            'fps': fps
        }
        
        pipeline.video_processor.release()
        print(f"  Frames: {frame_count}, Duration: {duration:.2f}s, FPS: {fps:.2f}")
    
    print("\n" + "-"*60)
    print("Performance Comparison Summary:")
    for model, data in results.items():
        print(f"  {model}: {data['fps']:.2f} FPS")


# Main execution
if __name__ == "__main__":
    import sys
    
    Logger.setup("logs")
    
    examples = {
        '1': ("Basic Video Processing", example_basic_video_processing),
        '2': ("Image Processing", example_image_processing),
        '3': ("Custom Configuration", example_custom_configuration),
        '4': ("Frame-by-Frame Processing", example_frame_by_frame_processing),
        '5': ("Webcam Real-time", example_webcam_processing),
        '6': ("Processing with Analytics", example_with_analytics),
        '7': ("Custom Drawing", example_custom_drawing),
        '8': ("Batch Processing", example_batch_processing),
        '9': ("Model Performance", example_performance_comparison),
    }
    
    print("\n" + "="*60)
    print("Lane Violation Detection - Advanced Examples")
    print("="*60)
    print("\nAvailable Examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  0. Run All")
    print("  q. Quit")
    
    choice = input("\nSelect example (0-9 or q): ").strip()
    
    if choice == '0':
        for key in sorted(examples.keys()):
            try:
                examples[key][1]()
            except Exception as e:
                print(f"Error in example: {str(e)}")
    elif choice == 'q':
        print("Exiting...")
        sys.exit(0)
    elif choice in examples:
        try:
            examples[choice][1]()
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("Invalid choice!")
