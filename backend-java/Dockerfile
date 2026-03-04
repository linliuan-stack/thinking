# ---- Stage 1: Build ----
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:resolve -q
COPY src ./src
RUN mvn package -DskipTests -q

# ---- Stage 2: Runtime ----
FROM eclipse-temurin:21-jre
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /build/target/module-service-1.0.0.jar app.jar

EXPOSE 8002
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8002/api/modules/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
