#!/usr/bin/env python3
"""CrowdStrike FalconPy RTR deployment scaffold for AgentLens endpoint collector."""
import argparse, os, sys
try:
    from falconpy import RealTimeResponse, RealTimeResponseAdmin
except Exception:
    print('Install falconpy: pip install crowdstrike-falconpy', file=sys.stderr); raise

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--host-id', action='append', required=True); ap.add_argument('--script-name', default='agentlens_install.sh'); ap.add_argument('--command', default='runscript')
    args=ap.parse_args()
    falcon=RealTimeResponse(client_id=os.environ['FALCON_CLIENT_ID'], client_secret=os.environ['FALCON_CLIENT_SECRET'])
    batch=falcon.batch_init_sessions(host_ids=args.host_id)
    print(batch)
    # Upload/install script using RealTimeResponseAdmin in production, then execute via batch_admin_command.
    print('Scaffold: upload signed AgentLens installer and run via RTR batch command.')
if __name__=='__main__': main()
