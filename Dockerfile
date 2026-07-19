FROM maven:3.9-eclipse-temurin-21

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Aquece o repositorio Maven e valida que o scaffold compila e sobe (SmokeTest)
COPY scaffold/backend /opt/scaffold/backend
RUN mvn -B -f /opt/scaffold/backend/pom.xml test \
    && mvn -B -f /opt/scaffold/backend/pom.xml clean

# Aquece node_modules do scaffold frontend
COPY scaffold/frontend /opt/scaffold/frontend
RUN cd /opt/scaffold/frontend && npm install --no-audit --no-fund

WORKDIR /bench
CMD ["python3", "/bench/agent/run_benchmark.py"]
