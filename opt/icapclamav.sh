#!/bin/sh

# Populating a ClamAV DB with a few signatures (to boot ClamAV)
echo "INFO: Filling a small CLamAV local DB..."
/bin/cat << 'EOF' > /var/lib/clamav/eicar.ndb
Eicar-Test-Signature:0:0:58354f2150254041505b345c505a58353428505e2937434329377d2445494341522d5354414e444152442d414e544956495255532d544553542d46494c452124482b482a
Eicar-Test-Signature-1:0:*:574456504956416c51454651577a5263554670594e54516f554634704e304e444b5464394a
EOF

# Managing rights on ClamAV Database Container Volume
chown -R clamav:clamav /var/lib/clamav/

# start clamd and c-icap service
echo "INFO: Starting up ClamD service..."
/usr/sbin/clamd

# Waiting for Clamd to start
echo "INFO: Waiting for Clamd to start..."
while : ; do
    [[ -S "/var/run/clamav/clamd.sock" ]] && break
    echo "...Waiting for ClamD to start..."
    sleep 1
done

# Updating our ClamAV Signatures Databases
echo "INFO: Updating the ClamAV Signatures DataBases..."
/usr/bin/freshclam -F --log=/var/log/clamav/freshclam-startup.log

# Start the icap service
echo "INFO: Starting up C-ICAP service"
/opt/c-icap/bin/c-icap -D -d 5

# start our FLASK APP
/usr/bin/python3 -m flask --app webicapscan.py run --host=0.0.0.0 &

exit 0