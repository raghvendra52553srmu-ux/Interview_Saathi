import { useState, useRef } from 'react';

const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null); // Final audio file
  const [duration, setDuration] = useState(0); // Timer
  
  const mediaRecorderRef = useRef(null);
  const timerRef = useRef(null);
  const chunksRef = useRef([]);

  // Start Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = []; // Clear old data

      // Jab data available ho (chunk by chunk)
      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      // Jab recording stop ho
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        chunksRef.current = [];
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      
      // Timer start karo
      setDuration(0);
      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, 1000);

    } catch (err) {
      console.error("Mic access denied:", err);
      alert("Please allow microphone access to record.");
    }
  };

  //  Stop Recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop Timer
      clearInterval(timerRef.current);
      
      // Stop all mic streams (Important to turn off red dot on browser tab)
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  // Reset Recording
  const resetRecording = () => {
    setAudioBlob(null);
    setDuration(0);
    setIsRecording(false);
  };

  return {
    isRecording,
    audioBlob,    // Ye backend pe bhejna hai
    duration,
    startRecording,
    stopRecording,
    resetRecording
  };
};

export default useAudioRecorder;
