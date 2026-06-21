#!/usr/bin/env python3
import argparse


def main():
    p = argparse.ArgumentParser(description="SentinelOne Remote Script Orchestration scaffold")
    p.add_argument("--site-id")
    p.add_argument("--agent-id", required=True)
    p.add_argument("--platform", choices=["macos", "linux", "windows"], default="macos")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    print({"vendor":"sentinelone", "agent_id":args.agent_id, "platform":args.platform, "execute":args.execute})
    print("TODO: call SentinelOne API to upload and execute the matching health check script")

if __name__ == "__main__":
    main()
