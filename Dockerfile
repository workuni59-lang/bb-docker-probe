FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends python3 ca-certificates procps iproute2 >/dev/null 2>&1 || true
COPY probe_runtime.py /probe_runtime.py
CMD ["python3","/probe_runtime.py"]
EXPOSE 8080
