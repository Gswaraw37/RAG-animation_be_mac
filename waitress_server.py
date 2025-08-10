from waitress import serve
from app import create_app
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start Waitress server"""
    
    # Create Flask app
    logger.info("Creating Flask application...")
    app = create_app()
    
    # Configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5001))
    threads = int(os.environ.get('THREADS', 4))  # Number of threads
    connection_limit = int(os.environ.get('CONNECTION_LIMIT', 100))
    cleanup_interval = int(os.environ.get('CLEANUP_INTERVAL', 30))
    
    logger.info("🚀 Starting Waitress Production Server")
    logger.info(f"📍 Host: {host}")
    logger.info(f"🔌 Port: {port}")
    logger.info(f"🧵 Threads: {threads}")
    logger.info(f"🔗 Connection Limit: {connection_limit}")
    logger.info(f"💾 Single Process Mode (Waitress)")
    logger.info("=" * 50)
    
    try:
        # Start Waitress server
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=connection_limit,
            cleanup_interval=cleanup_interval,
            channel_timeout=900,
	    recv_bytes=65536,
	    send_bytes=65536,
            log_socket_errors=True,
            clear_untrusted_proxy_headers=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise

if __name__ == '__main__':
    main()
