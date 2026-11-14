FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends curl python3 ca-certificates procps iproute2 >/dev/null 2>&1 || true
COPY probe2.py /probe2.py
RUN python3 /probe2.py || true
CMD ["python3","-m","http.server","8080"]
EXPOSE 8080
