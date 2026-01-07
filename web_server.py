"""Web Server Quick Start Script"""
import sys
from pathlib import Path

def main():
    print("\n" + "="*70)
    print(" Lane Violation Detection - Web Server Quick Start")
    print("="*70)
    
    print("\nPrerequisites:")
    print("  - Python 3.8+")
    print("  - Virtual environment activated")
    print("  - Dependencies installed (pip install -r requirements.txt)")
    
    print("\nStarting Web Server...")
    print("\nRunning: python run_server.py")
    print("\n" + "="*70)
    
    try:
        from app.server import create_app
        from src.utils.logger import Logger
        
        Logger.setup('logs')
        Logger.info("Starting web server...")
        
        app, server = create_app('configs/config.yaml', 5000)
        
        print("\n Web Server Started!")
        print("\n" + "="*70)
        print(" Open your browser and go to:")
        print(" http://localhost:5000")
        print("="*70)
        print("\nFeatures:")
        print("  - Upload videos/images")
        print("  - Real-time processing monitor")
        print("  - Real-time streaming from webcam/RTSP")
        print("  - View statistics and results")
        print("  - Configure system settings")
        print("  - Download processed videos")
        
        print("\nDocumentation:")
        print("  See GUIDE.md for full documentation")
        
        print("\nControls:")
        print("  Press Ctrl+C to stop the server")
        print("\n" + "="*70 + "\n")
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        
    except ImportError as e:
        print(f"\nError: Missing required packages")
        print(f"   {str(e)}")
        print("\nInstall dependencies with:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
