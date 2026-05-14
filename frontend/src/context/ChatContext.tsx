import React, { createContext, useContext, useState } from 'react';

interface ChatContextType {
  isChatActive: boolean;
  setChatActive: (active: boolean) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isChatActive, setChatActive] = useState(false);
  
  return (
    <ChatContext.Provider value={{ isChatActive, setChatActive }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
};