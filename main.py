"""Main entry point for the application"""
import argparse
import sys
from pathlib import Path

from src.pipeline import LaneViolationPipeline
from src.utils.logger import Logger


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Lane Violation Detection System'
    )
    parser.add_argument('--config', type=str, default='configs/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--input', type=str, default=None,
                       help='Input video file or camera index (overrides config)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output video file path (overrides config)')
    parser.add_argument('--image', type=str, default=None,
                       help='Process single image instead of video')
    parser.add_argument('--model', type=str, default=None,
                       help='YOLO model to use (overrides config)')
    
    args = parser.parse_args()
    
    try:
        # Create pipeline
        pipeline = LaneViolationPipeline(config_path=args.config)
        
        # Override config if arguments provided
        if args.input:
            pipeline.config.set('processing.input_source', args.input)
            pipeline.video_processor.input_source = args.input
        
        if args.output:
            pipeline.config.set('processing.output_path', args.output)
            pipeline.video_processor.output_path = args.output
        
        if args.model:
            pipeline.config.set('yolo.model_name', args.model)
        
        Logger.info("=" * 60)
        Logger.info("Lane Violation Detection System Started")
        Logger.info("=" * 60)
        
        # Process image or video
        if args.image:
            Logger.info(f"Processing image: {args.image}")
            output_image = args.output or str(Path(args.image).stem) + '_result.jpg'
            pipeline.process_image(args.image, output_image)
            Logger.info(f"Result saved to: {output_image}")
        else:
            Logger.info(f"Processing video: {pipeline.video_processor.input_source}")
            pipeline.run()
        
        Logger.info("=" * 60)
        Logger.info("Lane Violation Detection System Completed")
        Logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        Logger.error(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
