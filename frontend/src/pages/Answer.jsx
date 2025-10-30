import React, { useState } from "react";
import axiosClient from "../api/axiosClient";

export default function AnswerSubmit({ questionId }) {
  const [answer, setAnswer] = useState("");

  const submitAnswer = async () => {
    await axiosClient.post("/answers/", { question: questionId, content: answer });
    setAnswer("");
    alert("Answer submitted successfully!");
  };

  return (
    <div className="p-4 border rounded">
      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        className="w-full border p-2 rounded"
        placeholder="Write your answer..."
      />
      <button onClick={submitAnswer} className="mt-2 bg-green-600 text-white px-4 py-1 rounded">
        Submit
      </button>
    </div>
  );
}
