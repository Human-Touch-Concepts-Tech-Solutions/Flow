"use client";

import { useRef, useState, useEffect } from "react";
import { 
  Container, Content, Input, Wrapper, Funcbutton, Actions, 
  InputButtons, PreviewSec, InputWrap, Sendbutton 
} from "./UserInputStyles";
import { FiPaperclip, FiMic, FiSend, FiX } from "react-icons/fi";
import { RiSpeakAiLine } from "react-icons/ri";
import { AiOutlineLoading3Quarters } from "react-icons/ai";

export default function UserInput({ onSend }) {  // ← add this prop
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [fileError, setFileError] = useState("");
  const [notice, setNotice] = useState("");
  
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-expand textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length + files.length > 10) {
      setFileError("Maximum 1 file allowed.");
      return;
    }
    setFiles([...files, ...selectedFiles]);
    setFileError("");
    e.target.value = null;
  };

  const removeFile = (fileToRemove) => {
    setFiles(files.filter((f) => f !== fileToRemove));
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleUnavailable = (feature) => {
    setNotice(`${feature} is not available yet.`);
    setTimeout(() => setNotice(""), 3000);
  };

  // This is the new send handler – calls parent
const handleSendMessage = async () => {
  if (sending || (!message.trim() && files.length === 0)) return;

  const currentMessage = message;
  const currentFiles = [...files]; // This is definitely an array

  setMessage("");
  setFiles([]);
  setSending(true);

  try {
    // Pass the ARRAY, not files[0]
    await onSend(currentMessage, currentFiles); 
  } finally {
    setSending(false); 
  }
};
  return (
    <Container>
      <Content>
        <Wrapper onKeyDown={handleKeyDown}>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileSelect} 
            style={{ display: "none" }} 
            multiple
          />
          
          <InputWrap>
            <Input
              ref={textareaRef}
              rows={1}
              placeholder="Message Flowtru..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </InputWrap>

          {files.length > 0 && (
            <PreviewSec>
              {files.map((file) => (
                <div key={file.name} className="file-chip">
                  <span>{file.name}</span>
                  <button type="button" onClick={() => removeFile(file)}><FiX /></button>
                </div>
              ))}
            </PreviewSec>
          )}

          <Actions>
            <InputButtons>
              <Funcbutton type="button" onClick={() => fileInputRef.current.click()}>
                <FiPaperclip title="Attach File" />
              </Funcbutton>
              <Funcbutton type="button" onClick={() => handleUnavailable("Voice Input")}>
                <FiMic title="Voice Input" />
              </Funcbutton>
              <Funcbutton type="button" onClick={() => handleUnavailable("AI Voice")}>
                <RiSpeakAiLine title="AI Voice" />
              </Funcbutton>
            </InputButtons>

            <Sendbutton 
              onClick={handleSendMessage}  // ← changed here
              type="button" 
              disabled={sending || (!message.trim() && files.length === 0)}
            >
              {sending ? <AiOutlineLoading3Quarters className="spin" /> : <FiSend />}
            </Sendbutton>
          </Actions>

          {(fileError || notice) && (
            <p className="status-msg">{fileError || notice}</p>
          )}
        </Wrapper>
      </Content>
    </Container>
  );
}