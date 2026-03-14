// components/FileIcon.jsx
import { FiFile, FiFileText, FiImage, FiVideo, FiMusic } from "react-icons/fi";

export default function FileIcon({ fileName, size = 20 }) {
  // Add this guard clause to handle undefined or null
  if (!fileName || typeof fileName !== 'string') {
    return <FiFile size={size} />; 
  }

  const extension = fileName.split('.').pop().toLowerCase();
  switch (extension) {
    case 'pdf': return <FiFileText size={size} color="#ef4444" />; // Red
    case 'png': 
    case 'jpg': 
    case 'jpeg': return <FiImage size={size} color="#3b82f6" />; // Blue
    case 'mp4': return <FiVideo size={size} color="#8b5cf6" />;  // Purple
    case 'mp3': return <FiMusic size={size} color="#10b981" />;  // Green
    case 'docx': return <FiFileText size={size} color="#f59e0b" />; // Orange
    default: return <FiFile size={size} color="#94a3b8" />;      // Gray

  }
}