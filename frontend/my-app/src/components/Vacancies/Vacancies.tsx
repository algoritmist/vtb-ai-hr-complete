'use client';

import React, { useState, useEffect, useRef } from 'react';

export const Vacancies: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  
  // Буфер для накопления данных
  const audioBufferRef = useRef<Float32Array[]>([]);
  const bufferTimerRef = useRef<NodeJS.Timeout | null>(null);

  const BUFFER_DURATION = 3000;

  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    let interviewUuid = 'b74abe2f-ff91-4df6-9894-7b37591f37bd';
    const ws = new WebSocket(`ws://127.0.0.1:9300/ws?interview_uuid=${encodeURIComponent(interviewUuid)}`);
    ws.binaryType = 'arraybuffer';
    socketRef.current = ws;

    ws.onopen = () => console.log('✅ WS connected');
    
    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const blob = new Blob([event.data], { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        
        if (audioRef.current) {
          audioRef.current.src = url;
          audioRef.current.play().catch(e => console.error('Ошибка воспроизведения:', e));
        }
      }
    };

    ws.onclose = () => console.log('WS closed');
    ws.onerror = (e) => console.error('WS error', e);

    return () => {
      ws.close();
      stopRecording();
    };
  }, []);

  const startRecording = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      alert('WebSocket не подключен!');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const processor = ctx.createScriptProcessor(4096, 1, 1);
      scriptProcessorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        audioBufferRef.current.push(new Float32Array(inputData));
      };

      source.connect(processor);
      processor.connect(ctx.destination);

      bufferTimerRef.current = setInterval(() => {
        if (audioBufferRef.current.length > 0) {
          sendBufferedData();
        }
      }, BUFFER_DURATION);

      setIsRecording(true);
    } catch (err) {
      console.error('Ошибка доступа к микрофону:', err);
      alert('Не удалось получить доступ к микрофону');
    }
  };

  const sendBufferedData = () => {
    if (audioBufferRef.current.length === 0) return;

    const totalLength = audioBufferRef.current.reduce((sum, chunk) => sum + chunk.length, 0);
    const combinedData = new Float32Array(totalLength);
    let offset = 0;
    
    for (const chunk of audioBufferRef.current) {
      combinedData.set(chunk, offset);
      offset += chunk.length;
    }

    const int16Data = floatTo16BitPCM(combinedData);
    const buffer = int16Data.buffer;

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(buffer);
      console.log(`📤 Отправлено ${buffer.byteLength} байт аудиоданных`);
    }

    audioBufferRef.current = [];
  };

  const stopRecording = () => {
    if (audioBufferRef.current.length > 0) {
      sendBufferedData();
    }

    if (bufferTimerRef.current) {
      clearInterval(bufferTimerRef.current);
      bufferTimerRef.current = null;
    }

    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    setIsRecording(false);
  };

  function floatTo16BitPCM(input: Float32Array): Int16Array {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return output;
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">ИИ-ассистент</h1>

      <div className="mb-4">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg"
        >
          {isRecording ? 'Остановить запись' : 'Запустить микрофон'}
        </button>
      </div>
      <audio 
        ref={audioRef} 
        autoPlay 
        style={{ display: 'none' }}
      />
    </div>
  );
};