FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends curl python3 ca-certificates procps iproute2 >/dev/null 2>&1 || true
COPY probe.sh /probe.sh
RUN bash /probe.sh || true
CMD ["python3","-m","http.server","8080"]
EXPOSE 8080
