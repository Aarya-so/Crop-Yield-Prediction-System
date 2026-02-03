import { useState } from "react";
import "./App.css";

function App() {
  const [temperature, setTemperature] = useState("");
  const [humidity, setHumidity] = useState("");
  const [nitrogen, setNitrogen] = useState("");
  const [phosphorus, setPhosphorus] = useState("");
  const [potassium, setPotassium] = useState("");

  const [result, setResult] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    const response = await fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        temperature: Number(temperature),
        humidity: Number(humidity),
        nitrogen: Number(nitrogen),
        phosphorus: Number(phosphorus),
        potassium: Number(potassium),
      }),
    });

    const data = await response.json();
    setResult(data.recommended_crop);
  };

  return (
    <div className="container">
      <p className="heading">AIML Powered Yield Prediction System 🌾</p>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="number"
          className="input-field"
          placeholder="Temperature (°C)"
          value={temperature}
          onChange={(e) => setTemperature(e.target.value)}
          required
        />

        <input
          type="number"
          className="input-field"
          placeholder="Humidity (%)"
          value={humidity}
          onChange={(e) => setHumidity(e.target.value)}
          required
        />

        <input
          type="number"
          className="input-field"
          placeholder="Nitrogen (N)"
          value={nitrogen}
          onChange={(e) => setNitrogen(e.target.value)}
          required
        />

        <input
          type="number"
          className="input-field"
          placeholder="Phosphorus (P)"
          value={phosphorus}
          onChange={(e) => setPhosphorus(e.target.value)}
          required
        />

        <input
          type="number"
          className="input-field"
          placeholder="Potassium (K)"
          value={potassium}
          onChange={(e) => setPotassium(e.target.value)}
          required
        />

        <button type="submit">Predict Crop</button>
      </form>

      {result && (
        <div className="result">
          Recommended Crop: {result}
        </div>
      )}
    </div>
  );
}

export default App;
