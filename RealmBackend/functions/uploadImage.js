exports = async function(image){
  
    const collection = context.services.get("mongodb-atlas").db("etch").collection("images");
    await collection.insertOne({ image: image, status: "new" })
    return true;
};