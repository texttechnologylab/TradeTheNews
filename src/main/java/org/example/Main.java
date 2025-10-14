package org.example;

import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.UpdateOptions;
import org.apache.uima.fit.factory.JCasFactory;
import org.apache.uima.fit.util.JCasUtil;
import org.apache.uima.jcas.JCas;
import org.apache.uima.jcas.cas.FloatArray;
import org.bson.Document;
import org.bson.types.ObjectId;
import org.texttechnologylab.DockerUnifiedUIMAInterface.DUUIComposer;
import org.texttechnologylab.DockerUnifiedUIMAInterface.driver.DUUIDockerDriver;
import org.texttechnologylab.DockerUnifiedUIMAInterface.driver.DUUIRemoteDriver;
import org.texttechnologylab.DockerUnifiedUIMAInterface.driver.DUUIUIMADriver;
import org.texttechnologylab.DockerUnifiedUIMAInterface.lua.DUUILuaContext;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import static com.mongodb.client.model.Filters.eq;

//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
public class Main {

    public static void main(String[] args) throws Exception {
        DUUILuaContext lua = new DUUILuaContext().withJsonLibrary();
        DUUIComposer composer = new DUUIComposer()
                .withSkipVerification(true)
                .withLuaContext(lua)
                .withWorkers(5);

        DUUIDockerDriver docker = new DUUIDockerDriver();
        DUUIRemoteDriver remote = new DUUIRemoteDriver();
        DUUIUIMADriver uima = new DUUIUIMADriver();
        composer.addDriver(uima, docker, remote);

        composer.add(new DUUIRemoteDriver.Component("http://127.0.0.1:1000")); // embeddings
        composer.add(new DUUIRemoteDriver.Component("http://127.0.0.1:1001")); // llm scorer

        MongoDBHandler mh = new MongoDBHandler();
        MongoDatabase db = mh.getDatabase();
        MongoCollection<Document> articles = db.getCollection("articles");


        Document scoreNullFilter = new Document("llm_score", new Document("$eq", null));

        for (Document doc : articles.find(scoreNullFilter))
        {
            ObjectId id = doc.getObjectId("_id");
            String ticker = doc.getString("ticker");
            String title = cleanText(doc.getString("title"));
            String content = cleanText(doc.getString("content"));
            String summary = cleanText(doc.getString("summary"));
            String body;

            if (!content.isEmpty())
            {
                body = content;
            } else if (!summary.isEmpty())
            {
                body = summary;
            } else {
                body = "";
            }
            System.out.println(id + " " + ticker + " " + title + " " + body);
            JCas jCas = JCasFactory.createText(body, "de");

            LLMAnalysis llmAnalysis = new LLMAnalysis(jCas);
            llmAnalysis.setBegin(0);
            llmAnalysis.setEnd(body.length());
            llmAnalysis.setSymbol(ticker == null ? "" : ticker);
            llmAnalysis.setTitle(title);
            llmAnalysis.addToIndexes();

            try
            {
                composer.run(jCas);
            } catch (Exception e)
            {
                System.out.println(e.getMessage());
                continue;
            }

            List<Double> embedding = null;
            for (Embede emb : JCasUtil.select(jCas, Embede.class))
            {
                FloatArray floatArray = emb.getValues();
                if (floatArray != null)
                {
                    embedding = new ArrayList<>(floatArray.size());
                    for (int i = 0; i < floatArray.size(); i++)
                    {
                        embedding.add((double) floatArray.get(i));
                    }
                }
                break;
            }

            LLMAnalysis llm = JCasUtil.selectSingle(jCas, LLMAnalysis.class);


            Document set = new Document();
            if (embedding != null)
            {
                set.put("embedding", embedding);
                //            set.put("embedding_model", "sentence-transformers/all-MiniLM-L6-v2");
            }

            try
            {
                set.put("llm_score",    Integer.parseInt(llm.getScore()));
            } catch (Exception ignore)
            {
                set.put("llm_score",    0); // or null?
            }
            set.put("llm_reason",   llm.getReason());
            set.put("llm_prompt",   llm.getPrompt());
            set.put("llm_raw_json", llm.getRaw_json());
            set.put("analysedAt",   new Date());

            articles.updateOne(eq("_id", id), new Document("$set", set), new UpdateOptions().upsert(false));
        }
    }


    public static String cleanText(String input)
    {
        if (input == null) return "";
        input = input.replaceAll("[\\uD800-\\uDBFF](?![\\uDC00-\\uDFFF])", "")
                .replaceAll("(?<![\\uD800-\\uDBFF])[\\uDC00-\\uDFFF]", "");
        input = Normalizer.normalize(input, Normalizer.Form.NFC);
        input = input.replaceAll("\\s+", " ").trim();
        return input;
    }

}
