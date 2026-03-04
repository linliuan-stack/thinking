FROM eclipse-temurin:21-jre
WORKDIR /app
COPY target/module-service-1.0.0.jar app.jar
EXPOSE 8002
ENTRYPOINT ["java", "-jar", "app.jar"]
