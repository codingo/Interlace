_block:file-creation_
mkdir -p _output_/_target_/scans
mkdir _output_/_target_/exploit
mkdir _output_/_target_/loot
touch _output_/_target_/notes.txt
_block:file-creation_
_blocker_
_block_
echo "running Nikto scan on _target_"
nikto --host _target_ > _output_/_target_/scans/nikto-_target_.txt
_block_
_block_
echo "running SSLScan on _target_"
sslscan _target_ > _output_/_target_/scans/sslscan-_target_.txt
_block_
