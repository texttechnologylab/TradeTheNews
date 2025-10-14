StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")

function serialize(inputCas, outputStream, params)
  local cas = inputCas:getCas()
  local typeSystem = cas:getTypeSystem()
  local indexRepo = cas:getIndexRepository()
  local type = typeSystem:getType("org.example.LLMAnalysis")
  local iterableIndexFS = indexRepo:getAllIndexedFS(type)
  local featureStruct = iterableIndexFS:next()
  local outString = {
    title = featureStruct:getStringValue(type:getFeatureByBaseName("title")),
    symbol = featureStruct:getStringValue(type:getFeatureByBaseName("symbol")),
    summary = inputCas:getDocumentText()
  }
  outputStream:write(json.encode(outString))
end

function deserialize(inputCas, inputStream)
  local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)
  local results = json.decode(inputString)
  local item = ((results.items or {})[1]) or {}
  local cas = inputCas:getCas()
  local typeSystem = cas:getTypeSystem()
  local indexRepo = cas:getIndexRepository()
  local type = typeSystem:getType("org.example.LLMAnalysis")
  local iterableIndexFS = indexRepo:getAllIndexedFS(type)
  local featureStruct = iterableIndexFS:next()

  featureStruct:setStringValue(type:getFeatureByBaseName("text"), item.text)
  featureStruct:setStringValue(type:getFeatureByBaseName("score"), item.score)
  featureStruct:setStringValue(type:getFeatureByBaseName("reason"), item.reason)
  featureStruct:setStringValue(type:getFeatureByBaseName("prompt"), item.prompt)
  featureStruct:setStringValue(type:getFeatureByBaseName("raw_json"), item.raw_json)
end
