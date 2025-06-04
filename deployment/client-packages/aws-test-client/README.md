# LLM Firewall - Client Package for AWS Test Client

## Quick Start

1. Create logs directory:
   ```
   mkdir -p logs
   ```

2. Start the firewall:
   ```
   docker-compose up -d
   ```

3. Test the deployment:
   ```
   curl http://localhost:5001/health
   ```

For detailed instructions, see CLIENT_DEPLOYMENT.md

## Package Contents

- `docker-compose.yml` - Production deployment configuration
- `client_info_*.json` - License and build information
- `CLIENT_DEPLOYMENT.md` - Complete deployment guide
- `README.md` - This file

## Support

Contact your vendor for support and license renewals.
