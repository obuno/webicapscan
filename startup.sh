#!/bin/sh
chmod +x /opt/icapclamav.sh; sync && /opt/icapclamav.sh && exec /usr/sbin/crond -f -l 8
