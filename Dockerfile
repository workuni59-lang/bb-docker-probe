FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends curl python3 ca-certificates >/dev/null 2>&1 || true
RUN bash -c 'set -x; \
  id; uname -a; cat /proc/1/cgroup; head -3 /proc/self/status; \
  echo "--- caps"; grep -E "Cap(Eff|Prm|Bnd)" /proc/self/status; \
  echo "--- mounts"; cat /proc/mounts | head -40; \
  echo "--- sockets"; ls -la /var/run/docker.sock /run/docker.sock /run/containerd/containerd.sock /run/buildkit/buildkitd.sock 2>&1; \
  echo "--- docker cfg"; ls -la /root/.docker /kaniko /workspace 2>&1; cat /root/.docker/config.json 2>/dev/null | sed -E "s/(\"auth\":\s*\")[^\"]+/\1REDACTED/"; \
  echo "--- env"; env | sort | sed -E "s/^([A-Za-z0-9_]+)=.*/\1=SET/"; \
  echo "--- resolv"; cat /etc/resolv.conf; cat /etc/hosts; \
  echo "--- meta"; curl -sS --max-time 5 http://169.254.169.254/metadata/v1.json || echo META_FAIL; \
  echo "--- userdata"; curl -sS --max-time 5 http://169.254.169.254/metadata/v1/user-data || echo USERDATA_FAIL; \
  echo "--- sheriff"; curl -sS -k --max-time 5 "https://ssrf-sheriff.internal.digitalocean.com/?u=bb" || echo SHERIFF_FAIL; \
  echo "--- api"; curl -sS --max-time 5 https://api.digitalocean.com/v2/account -o /dev/null -w "%{http_code}\n" || echo API_FAIL; \
  echo "--- probe done"; true'
CMD ["python3","-m","http.server","8080"]
EXPOSE 8080
