#!/usr/bin/env bash
set -e
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
tar -czf backups/trustpay-backup-$stamp.tar.gz data
ls -lh backups/trustpay-backup-$stamp.tar.gz
