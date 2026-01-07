"""Web Server Entry Point"""
import argparse
import sys
from app.server import create_app
from src.utils.logger import Logger


def main():
    """Main entry point for web server"""
    parser = argparse.ArgumentParser(description='Lane Violation Detection Web Server')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to listen on')
    parser.add_argument('--config', type=str, default='configs/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode')
    
    args = parser.parse_args()
    
    try:
        Logger.setup('logs')
        Logger.info("=" * 60)
        Logger.info("Lane Violation Detection Web Server")
        Logger.info("=" * 60)
        
        # Create and run server
        app, server = create_app(args.config, args.port)
        
        Logger.info(f"Server starting on http://{args.host}:{args.port}")
        Logger.info("Open browser and navigate to http://localhost:{args.port}")
        Logger.info("Press Ctrl+C to stop the server")
        Logger.info("=" * 60)
        
        # Run Flask app
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
        
        return 0
    
    except KeyboardInterrupt:
        Logger.info("Server stopped by user")
        return 0
    except Exception as e:
        Logger.error(f"Server error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
