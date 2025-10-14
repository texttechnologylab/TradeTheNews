package org.example;



import com.mongodb.ConnectionString;
import com.mongodb.MongoClientSettings;
import com.mongodb.client.*;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class MongoDBHandler {
    private final MongoClient client;
    private final MongoDatabase database;

    public MongoDBHandler() {
        String user = System.getenv("DB_USER");
        String password = System.getenv("DB_PASSWORD");
        String host = System.getenv("DB_HOST");
        String port = System.getenv("DB_PORT");
        String db = System.getenv("DB_NAME");

        String encUser = URLEncoder.encode(user, StandardCharsets.UTF_8);
        String encPass = URLEncoder.encode(password, StandardCharsets.UTF_8);

        String connectionString = String.format("mongodb://%s:%s@%s:%s/%s", encUser, encPass, host, port, db);

        ConnectionString cs = new ConnectionString(connectionString);
        MongoClientSettings settings = MongoClientSettings.builder()
                .applyConnectionString(cs)
                .build();
        this.client = MongoClients.create(settings);
        this.database = client.getDatabase("StockForecast");
    }

    public MongoDatabase getDatabase() {
        return database;
    }


    public void close() {
        client.close();
    }

}
