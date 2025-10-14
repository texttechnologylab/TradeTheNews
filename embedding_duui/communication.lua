StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
utils = luajava.bindClass("org.apache.uima.fit.util.JCasUtil")

function serialize(inputCas, outputStream, params)
  local out =
  {
    doc_text = inputCas:getDocumentText()
  }
  outputStream:write(json.encode(out))
end


function deserialize(inputCas, inputStream)
  local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)
  local results = json.decode(inputString)
  local jcas = inputCas
  local cas = jcas:getCas()
  local typeSystem = cas:getTypeSystem()
  local indexRepo = cas:getIndexRepository()
  local vecType = typeSystem:getType("org.example.Embede")
  local fBegin = typeSystem:getFeatureByFullName("uima.tcas.Annotation:begin")
  local fEnd = typeSystem:getFeatureByFullName("uima.tcas.Annotation:end")
  local fValues = typeSystem:getFeatureByFullName("org.example.Embede:values")

  for x, item in ipairs(results["embeddings"] or {})
  do
    local vec = item["vector"]
    local n = #vec
    local float_arr = cas:createFloatArrayFS(n)

    for i=1,n
    do
        float_arr:set(i-1, vec[i])
    end

    local fs = cas:createFS(vecType)

    fs:setIntValue(fBegin, item["iBegin"] or 0)
    fs:setIntValue(fEnd, item["iEnd"] or 0)
    fs:setFeatureValue(fValues, float_arr)

    indexRepo:addFS(fs)
  end
end
