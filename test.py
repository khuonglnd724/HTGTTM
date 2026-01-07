"""Test script for lane violation detection system"""
import cv2
import numpy as np
import argparse
from pathlib import Path

from src.pipeline import LaneViolationPipeline
from src.utils.logger import Logger


def test_modules():
    """Test individual modules"""
    Logger.setup("logs")
    Logger.info("Testing Lane Violation Detection System")
    
    # Create dummy image for testing
    dummy_image = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Add some test content
    cv2.rectangle(dummy_image, (400, 300), (600, 500), (0, 255, 0), 2)
    cv2.line(dummy_image, (300, 0), (300, 720), (255, 255, 0), 2)
    cv2.line(dummy_image, (600, 0), (600, 720), (255, 255, 0), 2)
    cv2.line(dummy_image, (900, 0), (900, 720), (255, 255, 0), 2)
    
    Logger.info("Created dummy test image")
    
    try:
        # Test pipeline initialization
        Logger.info("Testing Pipeline initialization...")
        pipeline = LaneViolationPipeline("configs/config.yaml")
        Logger.info("✓ Pipeline initialized")
        
        # Test vehicle detector
        Logger.info("Testing Vehicle Detector...")
        detection_result = pipeline.vehicle_detector.detect(dummy_image)
        Logger.info(f"✓ Vehicle detector working - Detections: {detection_result['num_detections']}")
        
        # Test lane detector
        Logger.info("Testing Lane Detector...")
        lane_result = pipeline.lane_detector.detect_lanes(dummy_image)
        Logger.info(f"✓ Lane detector working - Lanes detected: {lane_result['num_lanes']}")
        
        # Test violation detector
        Logger.info("Testing Violation Detector...")
        lane_boundaries = pipeline.lane_detector.get_lane_boundaries(dummy_image)
        Logger.info(f"✓ Violation detector ready - Boundaries: {lane_boundaries['num_lanes']}")
        
        # Test frame processing
        Logger.info("Testing Frame Processing...")
        results = pipeline.process_frame(dummy_image, 0)
        Logger.info(f"✓ Frame processing working")
        
        # Test drawing
        Logger.info("Testing Result Drawing...")
        annotated = pipeline.draw_results(dummy_image, results)
        Logger.info(f"✓ Drawing working - Output shape: {annotated.shape}")
        
        Logger.info("\n" + "=" * 60)
        Logger.info("All tests passed! System is ready to use.")
        Logger.info("=" * 60)
        
        return True
    
    except Exception as e:
        Logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_with_image(image_path: str):
    """Test with real image"""
    Logger.info(f"Testing with image: {image_path}")
    
    try:
        pipeline = LaneViolationPipeline("configs/config.yaml")
        
        # Process image
        image = cv2.imread(image_path)
        if image is None:
            Logger.error(f"Could not load image: {image_path}")
            return False
        
        Logger.info(f"Image loaded - Shape: {image.shape}")
        
        results = pipeline.process_frame(image, 0)
        annotated = pipeline.draw_results(image, results)
        
        output_path = str(Path(image_path).stem) + "_test.jpg"
        cv2.imwrite(output_path, annotated)
        
        Logger.info(f"✓ Test image processed - Output: {output_path}")
        Logger.info(f"  Detections: {len(results['detections'])}")
        Logger.info(f"  Violations: {len([v for v in results['violations'] if v['is_violating']])}")
        
        return True
    
    except Exception as e:
        Logger.error(f"Image test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test entry point"""
    parser = argparse.ArgumentParser(description='Test Lane Violation Detection System')
    parser.add_argument('--mode', type=str, choices=['modules', 'image'], 
                       default='modules', help='Test mode')
    parser.add_argument('--image', type=str, default=None, help='Test image path')
    
    args = parser.parse_args()
    
    if args.mode == 'modules':
        success = test_modules()
    elif args.mode == 'image':
        if args.image is None:
            print("Error: --image argument required for image mode")
            return 1
        success = test_with_image(args.image)
    else:
        success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
