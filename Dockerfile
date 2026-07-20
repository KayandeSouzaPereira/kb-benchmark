FROM maven:3.9-eclipse-temurin-21

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Habilita o Dev MCP do Quarkus (lido de ~/.quarkus/dev-mcp.properties)
RUN mkdir -p /root/.quarkus && echo "enabled=true" > /root/.quarkus/dev-mcp.properties

# Aquece o repositorio Maven e valida que o scaffold compila e sobe (SmokeTest);
# tambem aquece as deps do quarkus:dev (usado no modo de avaliacao dev-mcp)
COPY scaffold/backend /opt/scaffold/backend
RUN mvn -B -f /opt/scaffold/backend/pom.xml test \
    && mvn -B -f /opt/scaffold/backend/pom.xml quarkus:go-offline -q || true
RUN mvn -B -f /opt/scaffold/backend/pom.xml clean

# Aquece node_modules do scaffold frontend
COPY scaffold/frontend /opt/scaffold/frontend
RUN cd /opt/scaffold/frontend && npm install --no-audit --no-fund

WORKDIR /bench
CMD ["python3", "/bench/agent/run_benchmark.py"]
